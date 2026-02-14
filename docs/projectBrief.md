# Project Brief: Open Table RPG

## Purpose

A backend API for organizing **open-table RPG sessions** -- the kind of tabletop RPG where players drop in and out across sessions, and a Game Master (GM) manages the group roster. The app handles **who can access which lobby** and **how players join/leave**, with strict separation between lobbies.

## Core Requirements

### Account System
- Two fixed account types: **GM** and **Player**.
- Only GMs can create lobbies. GMs cannot join other lobbies as players.
- If a person wants to be a player in someone else's lobby they need a separate player account with a different email (email is globally unique).
- Email + password authentication with cookie-based server-side sessions.

### Lobby System
- A GM creates a lobby and is automatically its DM (Dungeon Master) with `active` membership.
- Each lobby has exactly one DM.
- Players can belong to multiple lobbies via `LobbyMember` records.

### Invite System (Two Modes)
1. **Email invite (token link):** GM generates a single-use token URL bound to a specific email, expires in 7 days. The invited person signs up via the link and becomes a player in that lobby. No actual email sending -- the GM shares the link manually.
2. **User ID invite:** GM invites an existing player by their user ID. The player sees pending invites and can accept/decline.

### Membership Lifecycle
- **Invited** -> **Active** (on accept) or stays pending
- **Active** -> **Left** (player leaves voluntarily) or **Banned** (GM bans)
- **Banned** -> **Active** (GM unbans)
- Left members can be re-invited; banned members cannot be invited until unbanned.

### Moderation
- GMs can ban/unban players in their own lobby only (with optional `ban_reason`).
- Banned users lose access to lobby endpoints and cannot accept invites until unbanned.

### Authorization
- Strict per-lobby authorization: no cross-lobby or cross-GM control.
- All lobby-scoped endpoints verify caller authorization (DM vs member vs non-member).

## Problems Solved
- Organizing open-table RPGs where the player roster changes between sessions.
- Managing lobby membership, invites, and bans through a clean API.
- Enforcing clear GM/player boundaries and lobby isolation.

## User Experience Goals
- Clean REST API (FastAPI + OpenAPI/Swagger docs).
- Clear error messages (409 for duplicate email, 401/403 for auth, etc.).
- Atomic operations (no partial state on failures).
- Consistent invite lifecycle: pending -> accepted/declined/revoked/expired.

## Current Implementation Status

### Completed (US-001)
- GM registration endpoint (`POST /api/gm/register`)
- Login with cookie-based sessions (`POST /api/login`)
- Logout with session revocation (`POST /api/logout`)
- "Who am I" endpoint (`GET /api/whoami`)
- Password hashing with Argon2
- Email normalization and uniqueness enforcement

### Not Yet Implemented (US-002 through US-009)
- Lobby creation and details
- Email invite creation and acceptance
- User ID invite creation and accept/decline
- Player leaves lobby
- Ban/unban functionality
- Cross-lobby authorization enforcement
- Player account type (model only has `gm` in the AccountType enum)
- `updated_at` field on User model

## Non-Goals (Out of Scope for MVP)
- Email delivery (SMTP, templates, resend)
- Frontend / UI
- Password reset, email verification, MFA
- DM transfer, lobby deletion, lobby settings beyond name
- Multiple DMs per lobby
- Admin panel, global moderation
- GM participating as player with same account/email
