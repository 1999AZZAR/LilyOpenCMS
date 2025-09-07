# API Central Guide (Updated: 2025-09-05)

This single guide consolidates API docs, OpenAPI preview/validation, implementation summary, and examples for LilyOpenCMS.

## Contents
- Overview
- External Auth & Profile/Account API
- Public API Endpoints
- OpenAPI Preview & Validation
- Implementation Summary (what’s in code)
- Usage Examples (curl, JS, Python)
- Testing & Troubleshooting

---

## Overview
- REST API for news, albums/chapters, users, comments, ratings, media, SEO, and admin tools
- Public endpoints (no auth) under `/api/public/*`
- Authenticated endpoints via session or Bearer tokens
- Swagger UI at `/api/docs` (spec at `/api/openapi.yml`)

Servers in spec support a customizable server entry: choose scheme/host in Swagger UI.

---

## External Auth & Profile/Account API (Bearer)
New endpoints for mobile/third‑party clients (token auth via itsdangerous; access ~1h, refresh ~14d):
- POST `/api/auth/register`: create pending account
- POST `/api/auth/login`: returns `{access_token, refresh_token, token_type, expires_in, user}`
- POST `/api/auth/refresh`: exchange refresh token for new pair
- POST `/api/auth/logout`: stateless; client discards tokens
- GET `/api/auth/me`: current user

Profile & account CRUD parity:
- GET/PUT `/api/auth/profile`: user fields (first_name, last_name, email, birthdate, bio) + profile (pronouns, short_bio, location, website, social_links)
- PATCH `/api/auth/profile/privacy`: `show_email`, `show_birthdate`
- PATCH `/api/auth/profile/username`: requires `current_password`
- POST `/api/auth/account/change-password`: `current_password`, `new_password`, `confirm_password`
- DELETE `/api/auth/account`

Note: Use `Authorization: Bearer <access_token>`.

---

## Public API Endpoints (No Auth)
Highlights (full details in the OpenAPI spec):
- News: `GET /api/public/news/{id}`, `GET /api/public/news`
- Albums/Chapters: `GET /api/public/albums/{id}`, `GET /api/public/albums/{album_id}/chapters/{chapter_id}`, `GET /api/public/albums`
- User profile: `GET /api/public/user/{username}`, `/stats`, `/library`
- Categories/Tags: `GET /api/public/categories`, `GET /api/public/tags`
- Comments (read): `GET /api/public/comments/{content_type}/{content_id}`
- Search: `GET /api/public/search`

Premium items return limited info with a message.

---

## OpenAPI Preview & Validation
- Swagger UI (built‑in):
  - UI: `GET /api/docs`
  - Spec: `GET /api/openapi.yml`
  - UI selects servers; includes custom server with `{scheme}://{host}` variables
- Local previews:
  - Docker Swagger UI: `docker run -p 8080:8080 -e SWAGGER_JSON=/app/openapi.yml -v /home/azzar/project/exposeur/docs/openapi.yml:/app/openapi.yml swaggerapi/swagger-ui`
  - Redoc: `npx redoc-cli serve /home/azzar/project/exposeur/docs/openapi.yml --watch --port 8080`
  - Swagger UI watcher: `npx swagger-ui-watcher /home/azzar/project/exposeur/docs/openapi.yml --port 8080`
- Validation:
  - `npx redoc-cli lint /home/azzar/project/exposeur/docs/openapi.yml`
  - or `npx @stoplight/spectral-cli lint /home/azzar/project/exposeur/docs/openapi.yml`

---

## Implementation Summary
- Routes
  - Public API: `routes/routes_public_api.py`
  - External Auth/Profile API: `routes/routes_external_auth.py`
  - Swagger UI: `routes/routes_swagger.py` (UI at `/api/docs`, spec at `/api/openapi.yml`)
  - Registered in `routes/__init__.py`
- Tokens
  - itsdangerous signed tokens; access TTL ~1h, refresh TTL ~14d
  - Decorator: `token_required` validates Bearer tokens
- Models
  - `User` with role/flags; `UserProfile` with social_links, pronouns, privacy flags
- Docs
  - Spec: `docs/openapi.yml` (includes examples and cURL samples)
  - Reference: `docs/api.md` (overview tables)

---

## Usage Examples

### Login and call /me
```bash
curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"USER","password":"PASS"}' | jq .

curl -s http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

### Refresh token
```bash
curl -s -X POST http://localhost:5000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"REFRESH_TOKEN"}' | jq .
```

### Public search
```bash
curl "http://localhost:5000/api/public/search?q=test&type=all&page=1&per_page=20"
```

---

## Testing & Troubleshooting
- Run backend locally:
```bash
cd /home/azzar/project/exposeur
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python migrations/safe_migrate.py
python main.py
```
- Dev server: http://localhost:5000
- Swagger UI: http://localhost:5000/api/docs
- If you see a 400 with binary bytes in the log, a client attempted TLS on HTTP; terminate TLS at a proxy (Nginx) or use http:// during local dev.

---

## Roadmap Notes
- Done: External Auth/Profile endpoints; Swagger UI; spec examples; customizable servers
- Next: CI spec validation; optional spec generation pipeline
