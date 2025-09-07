# OpenAPI Local Preview & Validation Guide (Consolidated in API_CENTRAL.md)

This guide is now consolidated into `docs/API_CENTRAL.md`. The content below remains as a quick reference.

## Prerequisites
- Python virtualenv set up (optional but recommended)
- Node.js (for Redoc/Swagger UI without Docker)
- OR Docker (for Swagger UI container)

## Preview Option A: Docker (Swagger UI)
If Docker is installed, start the daemon and run Swagger UI:

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker

# Serve OpenAPI via Swagger UI on http://localhost:8080
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/app/openapi.yml \
  -v /home/azzar/project/exposeur/docs/openapi.yml:/app/openapi.yml \
  swaggerapi/swagger-ui
```

Open: http://localhost:8080

## Preview Option B: Node (no Docker)
Using Redoc (clean HTML docs):
```bash
npx redoc-cli serve /home/azzar/project/exposeur/docs/openapi.yml --watch --port 8080
```
Open: http://localhost:8080

Using Swagger UI Watcher (Swagger UI + live reload):
```bash
npx swagger-ui-watcher /home/azzar/project/exposeur/docs/openapi.yml --port 8080
```
Open: http://localhost:8080

## Preview Option C: Web Editor
- Open Swagger Editor: https://editor.swagger.io
- File → Import URL/File → select `docs/openapi.yml`

## Validate the OpenAPI YAML
Basic validation with Redoc CLI:
```bash
npx redoc-cli lint /home/azzar/project/exposeur/docs/openapi.yml
```
Or use Spectral (if installed):
```bash
npx @stoplight/spectral-cli lint /home/azzar/project/exposeur/docs/openapi.yml
```

## Run the Backend Locally
From project root:
```bash
cd /home/azzar/project/exposeur
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Initialize/verify DB (uses custom safe migration)
python migrations/safe_migrate.py

# (Optional) seed demo data
bash config/generate_test_data.sh

# Start server
export FLASK_ENV=development
python main.py
```
Server runs at: http://localhost:5000

## Quick API Smoke Tests
Public search:
```bash
curl "http://localhost:5000/api/search/news?q=test&type=general&page=1&per_page=12"
```
Public user profile:
```bash
curl "http://localhost:5000/api/public/user/demo"
```
Authenticated example (replace TOKEN):
```bash
curl -H "Authorization: Bearer TOKEN" http://localhost:5000/api/news | jq .
```

## Troubleshooting
- Docker not running: `sudo systemctl enable --now docker` then `newgrp docker`.
- Port already in use: pick another `--port` (e.g., 8081) or stop the existing process.
- Spec errors: open `docs/openapi.yml`, fix reported line; revalidate with the commands above.
