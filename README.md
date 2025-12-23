# Playlist Bridge

**Playlist Bridge** is a web app to connect a Google account and transfer playlists between Spotify and YouTube Music. It provides a FastAPI backend that handles OAuth for Google/YouTube and Spotify, persists tokens, and exposes endpoints to list playlists and transfer content between platforms.

---

## Table of Contents

- [Project overview](#project-overview)
- [Architecture](#architecture)
- [Backend endpoints](#backend-endpoints)
- [Authentication & cookies](#authentication--cookies)
- [Environment variables / Configuration](#environment-variables--configuration)
- [Database](#database)
- [Libraries & Tools Used](#libraries--tools-used)
- [Run & Development](#run--development)

---

## Project overview

Playlist Bridge helps users copy playlists from Spotify -> YouTube and from YouTube -> Spotify. The backend is implemented in Python using FastAPI and interacts with external provider APIs (Spotify and YouTube).

## Architecture

- Backend: FastAPI (async), exposes REST endpoints under the `/api` prefix.
- Frontend: Vite + React + TypeScript (located in `frontend/`).
- DB: Async SQLAlchemy, lightweight models for `users` and `oauth_accounts`.

---

## Backend endpoints

All backend routes are prefixed with `/api` (see `backend/app/main.py`).

### Health
- GET `/api/health`
  - Returns: `{ "status": "ok" }`
  - Usage: quick liveness check

### Authentication (Google)
- GET `/api/auth/google/login`
  - Starts OpenID Connect / Google login flow (redirects to Google).
- GET `/api/auth/google/callback`
  - Called by Google after login. Creates a user if needed and sets an `access_token` cookie (JWT). Redirects to the frontend (`FRONTEND_URL`).

> Note: The cookie name is `access_token` and is HttpOnly.

### User
- GET `/api/users/me`
  - Requires `access_token` cookie. Returns user object: `{ id, email, name, picture }`.
- POST `/api/users/logout`
  - Deletes the `access_token` cookie.

### OAuth provider connectors
- GET `/api/oauth/spotify/login`
  - Redirects user to Spotify's authorization page.
- GET `/api/oauth/spotify/callback`
  - Stores Spotify `access_token` / `refresh_token` and `expires_at` for the current user.

- GET `/api/oauth/youtube/login`
  - Redirects to Google OAuth with YouTube scope (requests offline access to get refresh token).
- GET `/api/oauth/youtube/callback`
  - Stores YouTube tokens for the current user.

All provider callbacks require an authenticated user (i.e., user must first sign in with Google to get the cookie).

### Provider playlist listing
- GET `/api/spotify/playlists`
  - Requires connected Spotify account; returns current user playlists via Spotify API.
- GET `/api/youtube/playlists`
  - Requires connected YouTube account; returns list of the user's YouTube playlists (id, name, count)

### Transfer endpoints
- POST `/api/transfer/spotify-to-youtube/{playlist_id}`
  - Description: Copies tracks from a Spotify playlist into a newly created YouTube playlist (private by default).
  - Path param: `playlist_id` (Spotify playlist ID)
  - Optional JSON payload: `{ "title": "Custom Title" }` to override target playlist title
  - Requirements: User must have both Spotify and YouTube connected
  - Response: `{ total, matched, skipped, youtube_playlist_id, errors }

- POST `/api/transfer/youtube-to-spotify/{playlist_id}`
  - Description: Reads video titles from a YouTube playlist and tries to match them to Spotify tracks, creating a new Spotify playlist and adding matched tracks.
  - Path param: `playlist_id` (YouTube playlist ID)
  - Optional JSON payload: `{ "title": "Custom Title" }`
  - Requirements: User must have both YouTube and Spotify connected
  - Response: `{ total, matched, skipped, spotify_playlist_id }

---

## Authentication & cookies

- After successful Google sign-in the backend sets a JWT cookie named `access_token` (HttpOnly).
- The `get_current_user` dependency in `app/api/deps.py` decodes the JWT and returns the `sub` claim (user id).
- OAuth tokens for third-party providers are stored in the `oauth_accounts` DB table with `access_token`, `refresh_token`, and `expires_at`.
- Tokens are refreshed automatically via `app/services/oauth_utils.py` when expired.

---

## Environment variables / Configuration

Set variables in `.env` (the project uses `pydantic_settings.BaseSettings`) or export them into your environment.

Important variables (see `app/core/config.py`):

- `PROJECT_NAME` - default "PlaylistBridge"
- `FRONTEND_URL` - where OAuth redirects after successful auth (e.g., `http://127.0.0.1:5173`)
- `DATABASE_URL` - SQLAlchemy async database URL (e.g., `sqlite+aiosqlite:///./dev.db`)
- `JWT_SECRET` - secret for JWT creation
- `JWT_ALGORITHM` - default `HS256`
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - for Google / YouTube auth
- `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` - for Spotify auth
- (`YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` appear in config but Google credentials are used for YouTube)

---

## Database

- Models: `User` and `OAuthAccount` (see `backend/app/models/`)
- Initialize DB: run `python -m backend.app.core.init_db` (or `python backend/app/core/init_db.py`) which executes SQLAlchemy metadata create_all using the configured `DATABASE_URL`.

---

## Libraries & Tools Used

Backend (Python):

- fastapi — web framework
- uvicorn — ASGI server
- sqlalchemy (async) — ORM / DB
- authlib — OAuth integration
- python-jose — JWT encode/decode
- spotipy — Spotify Web API client
- httpx — async HTTP client
- pydantic — data validation (via BaseModel)

Frontend (inside `frontend/`):

- vite — bundler / dev server
- react — UI library
- typescript — type system
- tailwindcss — styles
- axios — HTTP client

Third-party APIs: Spotify Web API, YouTube Data API v3, Google OpenID Connect

---

## Run & Development

1. Backend

- Install python dependencies (example virtualenv):

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r backend/requirements.txt
# Note: requirements.txt is minimal; you may need to install extra packages used in the code:
pip install authlib python-jose spotipy httpx sqlalchemy aiosqlite pydantic_settings

# Initialize DB
python backend/app/core/init_db.py

# Run dev server
uvicorn app.main:app --reload --factory --host 127.0.0.1 --port 8000
# Or: uvicorn app.main:app --reload
```

2. Frontend

```bash
cd frontend
npm install
npm run dev
```

3. OAuth redirect URLs / developer console

- Configure Google OAuth credentials to include `http://127.0.0.1:8000/api/auth/google/callback` and `http://127.0.0.1:8000/api/oauth/youtube/callback` as authorized redirect URIs.
- Configure Spotify redirect `http://127.0.0.1:8000/api/oauth/spotify/callback` in your Spotify app settings.

---
