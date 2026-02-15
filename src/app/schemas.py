from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models import AccountType, LobbyMemberStatus


class GMRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class WhoAmIResponse(BaseModel):
    user_id: str
    email: EmailStr
    display_name: str
    account_type: AccountType


class LobbyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class LobbyMemberResponse(BaseModel):
    user_id: str | None
    target_email: EmailStr | None
    status: LobbyMemberStatus
    is_dm: bool


class LobbyDetailResponse(BaseModel):
    id: str
    name: str
    created_by_user_id: str
    members: list[LobbyMemberResponse]


class EmailInviteCreateRequest(BaseModel):
    target_email: EmailStr


class EmailInviteCreateResponse(BaseModel):
    invite_url: str
    expires_in_seconds: int
