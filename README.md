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

Import popular films and their directors and writers from TMDb after setting
`TMDB_API_TOKEN` in `.env`:

```bash
docker compose exec backend uv run python manage.py import_tmdb --limit 20 --page 1
```

The command updates imported records by TMDb ID and preserves local ratings and
favorites. Imported films are published, and imported people receive unusable
passwords. French (`fr-FR`) is used by default, with missing localized fields
filled from English (`en-US`). Use `--movie-id ID` for one film,
`--language en-US` to force English, or `--dry-run` to validate an import without
saving it. Local records that conflict with a TMDb ID are never overwritten.

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

### Endpoints

- `GET /api/films/` and `GET /api/films/{id}/`: public film list and detail.
- `GET /api/authors/` and `GET /api/authors/{id}/`: public author list and detail.
- `PATCH /api/films/{id}/`: update a film as staff with `cinema.change_film`.
- `PATCH /api/films/{id}/archive/`: archive a film as staff with `cinema.change_film`.
- `PATCH /api/authors/{id}/`: update an author as staff with `cinema.change_author`.
- `DELETE /api/authors/{id}/`: delete an author without films as staff with `cinema.delete_author`.
- `POST /api/auth/register/`: create a spectator account.
- `POST /api/auth/login/`: return access and refresh JWTs.
- `POST /api/auth/refresh/`: rotate a refresh JWT and return a new token pair.
- `POST /api/auth/logout/`: blacklist a refresh JWT.
- `PUT /api/films/{id}/rating/`: create or update the current spectator's film rating.
- `PUT /api/authors/{id}/rating/`: create or update the current spectator's author rating.
- `POST /api/films/{id}/favorite/`: add a film to the current spectator's favorites.
- `DELETE /api/films/{id}/favorite/`: remove a film from the current spectator's favorites.
- `GET /api/me/favorites/`: list the current spectator's paginated favorites.

Send the access token as `Authorization: Bearer <access>`. Send the refresh token in
the `refresh` JSON field when refreshing or logging out. A successful refresh returns
a replacement refresh token and invalidates the previous one.

Rating requests use a JSON body containing an integer `score` from 1 to 5. Rating
and favorite endpoints require an authenticated user with the spectator role.

Film statuses use TMDb's values: `Rumored`, `Planned`, `In Production`,
`Post Production`, `Released`, and `Canceled`. TMDb imports preserve the remote
status, while locally created films default to `Planned`. Hoorcinema archival is
represented separately by the `is_archived` field and never changes the TMDb status.

## License

Hoorcinema is available under the [MIT License](LICENSE).
