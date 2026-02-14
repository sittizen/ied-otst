# PRD: Open Table RPG Sessions — User + Lobby Creation (MVP)

## Overview
Build the first slice of a web app that supports open-table RPG organization by implementing account creation, authentication, lobby creation, and lobby membership management via invites. This phase focuses strictly on “who can access which lobby” and “how players join/leave,” with strong separation between lobbies.

## Goals
- Enable a game master (GM) to create an account and create one or more lobbies they control.
- Enable a GM to invite players to a lobby via:
  - Email invite for new users (token link; no outbound email sending in scope)
  - User ID invite for existing users (pending invites list + accept/decline)
- Enable invited players to create accounts via invite link and join the lobby.
- Enable players to leave a lobby.
- Enable GMs to ban/unban players in their own lobbies.
- Enforce strict authorization boundaries: no cross-lobby or cross-GM control.

## Quality Gates
These commands must pass for every user story:
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest`

## Scope / Product Decisions
- **API surface:** Backend API only (FastAPI + OpenAPI + JSON).
- **Framework:** FastAPI.
- **DB:** PostgreSQL.
- **ORM/migrations:** SQLAlchemy + Alembic.
- **Auth:** Email + password, cookie-based sessions (server-side session store).
- **Account types (fixed):** `gm` or `player`.
  - Only `gm` accounts can create lobbies.
  - `gm` accounts cannot join other lobbies as players.
  - If a person wants to be a player in someone else’s lobby, they must have a separate *player* account created via invite (and must use a different email because email is globally unique).
- **Email uniqueness:** Global unique across all users.
- **Invite rules:** Token link is single-use, expires in 7 days, and is bound to a specific email (signup email must match).
- **Re-invite / rejoin:** Users who left can be re-invited; banned users cannot be invited/accepted until ban is lifted.
- **Timestamps:** `created_at/updated_at` everywhere + optional `ban_reason`.

## Core Data Model (Conceptual)
Note: exact columns/types can vary, but behavior must match.

### User
- `id`
- `email` (unique)
- `password_hash`
- `display_name`
- `account_type` (`gm` | `player`)
- `created_at`, `updated_at`

### Lobby
- `id`
- `name`
- `created_by_user_id` (must be `gm` account_type user id)
- `created_at`, `updated_at`

### LobbyMember
- `lobby_id`
- `user_id`
- `status` (`invited` | `active` | `banned` | `left`)
- `created_at`, `updated_at`
- `banned_at` (nullable), `ban_reason` (nullable)
- `left_at` (nullable)

### Invite
Supports two target modes.
- `id`
- `lobby_id`
- `token` (unique, random) — used for email-link acceptance; may still exist for user_id invites for consistency/auditing
- `target_email` (nullable)
- `target_user_id` (nullable)
- `status` (`pending` | `accepted` | `declined` | `revoked` | `expired`)
- `created_by_user_id` (the GM)
- `created_at`, `updated_at`
- `expires_at`
- `used_at` (nullable)

Constraints/notes:
- Exactly one of `target_email` or `target_user_id` must be set.
- Invites are single-use: once `accepted/declined/revoked/expired`, they cannot be reused.

## User Stories

### US-001: GM account registration + session login/logout
**Description:** As a GM, I want to create an account and log in so that I can manage my lobbies.

**Acceptance Criteria:**
- [ ] API supports GM registration with `email`, `password`, `display_name`.
- [ ] Email is enforced as globally unique (clear 409-style error).
- [ ] Password is stored as a secure hash (no plaintext).
- [ ] API supports login that creates a server-side session and sets a cookie.
- [ ] API supports logout that invalidates the session.
- [ ] “Who am I” endpoint returns the authenticated user identity and account_type.

### US-002: Lobby creation (GM-only) + auto-membership as DM
**Description:** As a GM, I want to create a lobby so that I can run an open table.

**Acceptance Criteria:**
- [ ] Only authenticated `gm` users can create lobbies.
- [ ] Creating a lobby auto-creates a `LobbyMember` row for the GM with `status=active`.
- [ ] Each lobby has exactly one `dm` member (enforced by constraints or application logic).
- [ ] API can fetch lobby details for members of that lobby.

### US-003: Invite a new player by email (token link; no sending)
**Description:** As a GM, I want to create an email invite so that a new player can sign up and join my lobby.

**Acceptance Criteria:**
- [ ] Only the lobby’s GM (dm) can create invites for that lobby.
- [ ] Invite creation returns an invite URL containing a token (no email delivery required).
- [ ] Invite token is single-use and expires in 7 days.
- [ ] Invite is bound to a specific `target_email`.
- [ ] If `target_email` already belongs to an existing user, invite-by-email is rejected with a clear error directing the GM to use user_id invites instead.
- [ ] A corresponding `LobbyMember` entry is created/updated to reflect `status=invited` for that target (implementation detail allowed; behavior must match: lobby shows as invited, not active).

### US-004: Accept email invite — player signs up and becomes active member
**Description:** As an invited player, I want to use the invite link to create my account so that I can join the lobby.

**Acceptance Criteria:**
- [ ] Invite acceptance endpoint validates: token exists, status is pending, not expired, not used.
- [ ] Signup email must exactly match the invite’s `target_email` (case normalization rules must be defined and consistent).
- [ ] On success: create a `player` user account, mark invite `accepted`, mark membership `active`.
- [ ] Acceptance is atomic (no partial state if DB errors occur).
- [ ] If the lobby membership is currently `banned`, acceptance is blocked until unbanned.

### US-005: Invite an existing user by user_id (pending invites)
**Description:** As a GM, I want to invite an existing player by user_id so that they can accept from their account.

**Acceptance Criteria:**
- [ ] Only the lobby’s GM (dm) can create user_id invites for that lobby.
- [ ] The target user must exist and must be `account_type=player` (reject inviting a `gm` account).
- [ ] Creating the invite results in a `pending` invite tied to `target_user_id`.
- [ ] The invited user can see the invite in a “pending invites” API response.
- [ ] If the user is banned in that lobby, invite creation is rejected until ban is lifted.

### US-006: Existing player accepts/declines a pending invite
**Description:** As an existing player, I want to accept or decline pending invites so that I control which lobbies I join.

**Acceptance Criteria:**
- [ ] Authenticated player can list their pending invites.
- [ ] Accepting an invite makes the player an `active` `LobbyMember` of that lobby and marks invite `accepted`.
- [ ] Declining an invite marks invite `declined` and does not create an active membership.
- [ ] Users cannot accept/decline invites that don’t target them.
- [ ] Accept/decline fails cleanly for revoked/expired/used invites.

### US-007: Player leaves a lobby
**Description:** As a player, I want to leave a lobby so that I can stop participating.

**Acceptance Criteria:**
- [ ] An active player can leave a lobby, changing membership to `status=left` and setting `left_at`.
- [ ] After leaving, the user no longer has access to lobby-protected endpoints for that lobby.
- [ ] The lobby’s DM cannot be “left” via this endpoint (returns clear error).

### US-008: GM bans and unbans players in their lobby
**Description:** As a GM, I want to ban/unban players so that I can moderate my lobby.

**Acceptance Criteria:**
- [ ] Only the lobby’s DM can ban/unban members of that lobby.
- [ ] Banning sets `status=banned`, `banned_at`, and optional `ban_reason`.
- [ ] Unbanning restores `status=active` only if the prior state was banned; timestamps update accordingly.
- [ ] Banned users cannot access lobby-protected endpoints.
- [ ] Banned users cannot be invited or accept invites until unbanned.

### US-009: Authorization and tenancy enforcement (cross-lobby safety)
**Description:** As the system, I must enforce permissions so that no GM can affect another GM’s lobby.

**Acceptance Criteria:**
- [ ] All lobby-scoped endpoints verify the caller is authorized for that lobby (DM vs member vs non-member).
- [ ] Attempts to manage invites/members in other lobbies return 403/404 (pick one approach and apply consistently).
- [ ] Automated tests cover: cross-lobby access denial, DM-only actions, banned user restrictions, expired invite behavior.

## Functional Requirements
- FR-1: The system must support two fixed user account types: `gm` and `player`.
- FR-2: Only `gm` users can create lobbies.
- FR-3: A lobby must always have exactly one DM membership, created automatically on lobby creation.
- FR-4: The system must support email-based invites for new users using single-use tokens bound to email and expiring in 7 days.
- FR-5: The system must support user_id-based invites for existing users with explicit accept/decline.
- FR-6: Email is globally unique across all users.
- FR-7: Players can belong to multiple lobbies (membership via `LobbyMember` only; no `User.lobby_id` field).
- FR-8: Players can leave lobbies; DMs cannot leave their own lobby in MVP.
- FR-9: DMs can ban/unban players in their own lobby only; bans block access and acceptance/invites.
- FR-10: All membership/invite/user/lobby records must track `created_at/updated_at`; bans include optional `ban_reason`.

## Non-Goals (Out of Scope)
- Sending emails (SMTP/provider integration), templates, resend flows.
- UI/frontend pages (signup forms, lobby screens).
- Password reset, email verification, MFA.
- DM transfer, lobby deletion, lobby settings beyond name.
- Multiple DMs per lobby.
- Admin panel, moderation across lobbies, global bans.
- “GM account participates as player elsewhere using same account/email” (explicitly disallowed).

## Technical Considerations (Implementation Guidance)
- Use FastAPI with OpenAPI schemas for all request/response models.
- Use PostgreSQL with SQLAlchemy models and Alembic migrations for all schema changes.
- Cookie sessions require:
  - Secure session ID cookie settings (HttpOnly, SameSite, Secure in prod)
  - Server-side session persistence (DB table) with expiration
  - CSRF strategy for state-changing endpoints (document chosen approach)
- Password hashing: use a modern KDF (argon2/bcrypt) and constant-time comparisons.
- Ensure invite acceptance and membership updates are transactional and idempotent where possible.
- Indexes recommended: `users.email`, `invites.token`, `lobby_members (lobby_id, user_id)` unique, `invites (lobby_id, target_email/target_user_id, status)` as needed.

## Success Metrics
- All defined user stories pass their acceptance criteria with automated tests.
- No cross-lobby privilege escalation in tests (DM cannot affect other lobbies).
- Invite lifecycle behaves correctly: pending → accepted/declined/revoked/expired; single-use enforced.
- Bans reliably block access and joining.

## Open Questions
- Should API return 403 vs 404 for unauthorized lobby access (leak vs usability)?
- Should “left” members be able to view lobby history/metadata at all (currently no)?
- Should user_id invites require a token at acceptance time, or rely solely on authenticated identity + invite id?
