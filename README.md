# Chameleon Table

Distributed turn-based multiplayer card game inspired by Coloretto. Built with
FastAPI, WebSockets and React for the Distributed Systems course at UniBo.

Players (2 to 5) create or join a room via a room code. A central server keeps
the authoritative game state, validates every action, enforces turn order and
broadcasts updates in real time. Spectators can watch an ongoing match without
interacting.

## Architecture

- **Backend** — FastAPI. REST for room management and state snapshots,
  WebSocket for real-time state push.
- **State store** — Redis is the authoritative store; PostgreSQL holds a
  snapshot used to recover a match after a server crash.
- **Frontend** — React + Zustand.
- **Deployment** — Docker Compose behind Nginx.

The compose setup is split in three files:

| File | Purpose |
| --- | --- |
| `docker-compose.yml` | Base. Only Nginx is reachable from the host. |
| `docker-compose.override.yml` | Development. Publishes Postgres and Redis on localhost so the test suite can reach them. Loaded automatically. |
| `docker-compose.prod.yml` | Production. Adds HTTPS on 443 and mounts the Let's Encrypt certificates. |

## Running locally

Requires Docker and Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Then open <http://localhost>.

Edit `.env` before the first run — `SECRET_KEY` must be replaced with a random
value, for example one generated with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"    # Windows
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # Linux / macOS
```

Set `REGISTRATION_ENABLED=false` to close new sign-ups on a public deployment.

## Seeding test users

With the stack running, this creates five ready-to-use accounts
(`player1`…`player5`, all with password `password123`):

```bash
python scripts/seed_db_nodeps.py    # Windows
python3 scripts/seed_db_nodeps.py   # Linux / macOS
```

It uses only the standard library, so it runs on any base Python 3 install with
nothing to install first. Registering an existing user is skipped, so the script
is safe to re-run. It needs `REGISTRATION_ENABLED=true`.

## Running the tests

86 tests: unit, integration, and fault-tolerance/timing.

The suite runs outside the containers and talks to Postgres and Redis over
localhost, which `docker-compose.override.yml` publishes automatically.

On Windows PowerShell:

```powershell
docker compose up -d db redis

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
pytest -v
```

On Linux / macOS:

```bash
docker compose up -d db redis

python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pytest -v
```

`conftest.py` sets `TESTING=1` itself, which isolates the run from development
data: Redis uses logical database 1 instead of 0, and PostgreSQL a separate
`chameleon_test` database, created automatically on first run. No manual setup
is needed on a fresh clone.