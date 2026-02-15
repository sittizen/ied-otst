# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

*Add reusable patterns discovered during development here.*

- Lobby-scoped endpoints should compose `get_current_user` with a direct `LobbyMember` lookup (`lobby_id` + `user_id`) and return `403` when the caller is not a member.

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
