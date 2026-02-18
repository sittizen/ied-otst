# High-Level Domain Model

## Core Entities

- Users can be either game masters or players
- A game master creates an account on the system
- A game master can create a lobby
- A game master can invite players into a lobby ( via email for new users, or user_id for existing ones )
- Players create their account following the invite link
- Players can leave a lobby
- Game masters can ban players from a lobby
- Bans can be lifted
- A game master has no agency of any kind on other game masters lobby
- A game master need to create another account via invite if he wants to also be a player in someone else lobby

### User

-   id
-   email
-   password_hash
-   display_name
-   lobby_id

### Lobby

-   id
-   name

### LobbyMember

-   lobby_id
-   user_id
-   role (dm \| player)
-   status (invited \| active \| banned \| left)

### Invite

-   id
-   lobby_id
-   token
-   target_user_id_or_email
-   status

------------------------------------------------------------------------

## Chat Domain

### ChatMessage

-   id
-   lobby_id
-   channel_type (room \| pm)
-   channel_id
-   author_id
-   body
-   created_at

------------------------------------------------------------------------

## Calendar Domain

### SessionEvent

-   id
-   lobby_id
-   title
-   description
-   starts_at
-   ends_at
-   created_by

### SessionRSVP

-   session_id
-   user_id
-   status (yes \| no \| maybe)
-   updated_at

------------------------------------------------------------------------

## Map Domain

### MapAsset

-   id
-   lobby_id
-   type (world)
-   file_url
-   version
-   uploaded_by
-   uploaded_at

### MapPin

-   id
-   map_asset_id
-   x
-   y
-   label
-   description

------------------------------------------------------------------------

## Journal Domain

### JournalEntry

-   id
-   lobby_id
-   author_id
-   title
-   body
-   visibility (lobby \| private)
-   created_at
-   updated_at
