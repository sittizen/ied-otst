# Ralph Progress Log

This file tracks progress across iterations. Agents update this file
after each iteration and it's included in prompts for context.

## Codebase Patterns (Study These First)

*Add reusable patterns discovered during development here.*

- FastAPI server-side sessions: store sessions in DB (`app/models.py` `Session`) and use `Cookie(alias=settings.session_cookie_name)` + `app/security.py:get_user_for_session()` for auth.

---


## 2026-02-14 - US-001
- Implemented GM registration (`POST /api/gm/register`) with unique email enforcement (409) and secure password hashing.
- Implemented login (`POST /api/login`) that creates a DB-backed session and sets an HttpOnly cookie.
- Implemented logout (`POST /api/logout`) that revokes the session and deletes the cookie.
- Implemented whoami (`GET /api/whoami`) returning authenticated user identity including `account_type`.
- Files changed: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `app/config.py`, `app/db.py`, `app/models.py`, `app/schemas.py`, `app/security.py`, `app/deps.py`, `app/routers/auth.py`, `app/main.py`
- **Learnings:**
  - Repo had no backend scaffold yet; created a minimal FastAPI + SQLAlchemy base to support auth/session endpoints.
  - `ruff`'s B008 rule conflicts with common FastAPI dependency patterns; ignored B008 in `pyproject.toml`.
  - Avoided `passlib`+`bcrypt` due to runtime incompatibilities; used `argon2-cffi` directly for password hashing/verification.
---
