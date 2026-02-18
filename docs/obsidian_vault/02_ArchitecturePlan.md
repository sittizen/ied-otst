# Architecture Plan

## System Overview

-   Single Python backend service
-   Relational database (PostgreSQL)
-   Object storage for map assets
-   Redis for WebSocket pub/sub
-   Browser-based frontend with minimal TUI-like UI

------------------------------------------------------------------------

## Deployment Model

### Environments

-   Local (Docker Compose)
-   Staging
-   Production

### Infrastructure

-   Managed PostgreSQL
-   Managed object storage
-   Containerized backend
-   Reverse proxy with HTTPS

------------------------------------------------------------------------

## Non-Functional Requirements

-   Support up to 100 concurrent users
-   Rate limiting for abuse prevention
-   Hourly database backups
-   Structured logging and error monitoring
