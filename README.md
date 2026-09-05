# Hoorcinema

Hoorcinema is a Django REST Framework and React application backed by PostgreSQL.

## Requirements

- Docker with Docker Compose
- Optional for local development: Python 3.13+, `uv`, Node.js 24, and npm

## Start with Docker

Copy `.env.example` to `.env` if you want to override the development defaults, then run:

```bash
docker compose up --build
```

The services are available at:

- Web application: <http://localhost:5173>
- Health API: <http://localhost:8000/api/health/>
- Hello API: <http://localhost:8000/api/hello/>
- Django administration: <http://localhost:8000/admin/>

The backend waits for PostgreSQL, applies migrations, and starts Django. Create an administrator with:

```bash
docker compose exec backend uv run python manage.py createsuperuser
```

Create the demo author, spectator, and administrator with passwords configured in
`.env`:

```bash
docker compose exec backend uv run python manage.py seed_demo_data
```

The required variables are `DEMO_AUTHOR_PASSWORD`, `DEMO_SPECTATOR_PASSWORD`, and
`DEMO_ADMIN_PASSWORD`. The command is idempotent and uses the usernames
`demo_author`, `demo_spectator`, and `demo_admin`.

## Tests and quality checks

Run backend checks in its container:

```bash
docker compose run --rm backend uv run ruff format --check .
docker compose run --rm backend uv run ruff check .
docker compose run --rm backend uv run pytest
```

Run frontend checks in its container:

```bash
docker compose run --rm frontend npm run format:check
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npm run typecheck
docker compose run --rm frontend npm run test -- --run
docker compose run --rm frontend npm run build
```

## API

### `GET /api/health/`

Returns a lightweight application liveness status:

```json
{"status": "ok"}
```

### `GET /api/hello/`

Returns the message displayed by the frontend:

```json
{"message": "Hello, World!"}
```
