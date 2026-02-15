from __future__ import annotations

from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import AccountType, Lobby, LobbyMember, LobbyMemberStatus, User
from app.schemas import LobbyCreateRequest, LobbyDetailResponse, LobbyMemberResponse

router = APIRouter(prefix="/api/lobbies", tags=["lobbies"])


def _to_lobby_detail_response(lobby: Lobby, members: Sequence[LobbyMember]) -> LobbyDetailResponse:
    dm_count = sum(1 for member in members if member.is_dm)
    if dm_count != 1:
        raise HTTPException(status_code=500, detail="Lobby DM invariant violated")

    return LobbyDetailResponse(
        id=lobby.id,
        name=lobby.name,
        created_by_user_id=lobby.created_by_user_id,
        members=[
            LobbyMemberResponse(user_id=member.user_id, status=member.status, is_dm=member.is_dm)
            for member in members
        ],
    )


@router.post("", status_code=201, response_model=LobbyDetailResponse)
def create_lobby(
    payload: LobbyCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LobbyDetailResponse:
    if user.account_type != AccountType.GM:
        raise HTTPException(status_code=403, detail="Only GMs can create lobbies")

    lobby = Lobby(name=payload.name, created_by_user_id=user.id)
    db.add(lobby)
    db.flush()

    dm_member = LobbyMember(
        lobby_id=lobby.id,
        user_id=user.id,
        status=LobbyMemberStatus.ACTIVE,
        is_dm=True,
    )
    db.add(dm_member)
    db.commit()

    db.refresh(lobby)
    db.refresh(dm_member)
    return _to_lobby_detail_response(lobby, [dm_member])


@router.get("/{lobby_id}", response_model=LobbyDetailResponse)
def get_lobby_details(
    lobby_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LobbyDetailResponse:
    lobby = db.get(Lobby, lobby_id)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")

    membership_stmt = select(LobbyMember).where(
        LobbyMember.lobby_id == lobby_id,
        LobbyMember.user_id == user.id,
    )
    membership = db.execute(membership_stmt).scalars().first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this lobby")

    members_stmt = select(LobbyMember).where(LobbyMember.lobby_id == lobby_id)
    members = db.execute(members_stmt).scalars().all()

    return _to_lobby_detail_response(lobby, members)
