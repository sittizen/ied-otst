# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

*Add reusable patterns discovered during development here.*

- Lobby-scoped endpoints should compose `get_current_user` with a direct `LobbyMember` lookup (`lobby_id` + `user_id`) and return `403` when the caller is not a member.
- Use invite placeholders in `LobbyMember` for pre-registration users: set `user_id=None`, store `target_email`, and set `status=invited` so lobby membership state is visible before account creation.

---


## [2026-02-15] - US-002
- Implemented GM-only lobby creation endpoint (`POST /api/lobbies`) that auto-creates the GM as an active DM lobby member.
- Implemented lobby details endpoint (`GET /api/lobbies/{lobby_id}`) with member-only authorization checks.
- Added lobby domain models and schemas (`Lobby`, `LobbyMember`, `LobbyMemberStatus`) and wired the lobbies router into app startup.
- Files changed:
  - `src/app/models.py`
  - `src/app/schemas.py`
  - `src/app/routers/lobbies.py`
  - `src/main.py`
  - `.ralph-tui/progress.md`
- **Learnings:**
  - Patterns discovered
    - Existing auth pattern uses dependency-injected DB/user context and explicit `HTTPException` errors; lobby routes follow the same style.
  - Gotchas encountered
    - `docs/techContext.md` is referenced in agent instructions but is not present in the repository, so implementation used existing code patterns plus `docs/systemPatterns.md` and `docs/projectBrief.md`.
---


## [2026-02-15] - US-003
- What was implemented
  - Added email invite creation endpoint at `POST /api/lobbies/{lobby_id}/invites/email` with DM-only authorization, existing-user rejection, and invite URL return containing a generated token.
  - Added an `Invite` model storing token hash, expiry (`7 days`), target email, creator, and `used_at` for single-use tracking.
  - Extended lobby membership representation to support invited-by-email entries (`LobbyMember.status=invited` plus `target_email`) and upsert behavior on repeated invites.
- Files changed
  - `src/app/models.py`
  - `src/app/schemas.py`
  - `src/app/routers/lobbies.py`
  - `.ralph-tui/progress.md`
- **Learnings:**
  - Patterns discovered
    - Reusing `LobbyMember` for pending email invites keeps lobby state consistent and avoids a separate pending-members projection layer.
  - Gotchas encountered
    - `docs/techContext.md` is referenced by agent instructions but does not exist in this repo.
    - Running `uv run mypy src` currently fails in this environment due unresolved third-party imports (`fastapi`, `sqlalchemy`, `pydantic`, etc.), unrelated to this story’s code changes.
---
