# HIMA application backend

Typed Django REST Framework backend managed with [`uv`](https://docs.astral.sh/uv/)
and PostgreSQL.

## Setup

Install `uv`, then create the environment and install application plus development
dependencies:

```shell
uv sync
cp .env.example .env
docker run --name hima-postgres \
  -e POSTGRES_DB=hima \
  -e POSTGRES_USER=hima \
  -e POSTGRES_PASSWORD=hima \
  -p 5432:5432 \
  -d postgres:16
uv run python src/manage.py migrate
uv run python src/manage.py runserver
```

The Django settings load `.env` automatically. Environment variables already
exported by the shell or CI take precedence over values in `.env`.

The PostgreSQL container is only needed once; start it again with
`docker start hima-postgres` on subsequent runs.

The health endpoint is available at `GET /api/v1/health/`.

## Inspecting PostgreSQL with pgweb

pgweb provides a browser-based interface for inspecting and querying the
PostgreSQL database. Start it after PostgreSQL is running:

```shell
pgweb \
  --host localhost \
  --port 5432 \
  --user hima \
  --pass hima \
  --db hima \
  --listen 1234
```

Open `http://localhost:1234` in your browser. Replace the connection values with
the database settings from your `.env` file if they differ from the local setup.

- pgweb connects to the database on port `5432` and serves its web interface on
  port `1234`.
- Keep pgweb local and stop it when you are done; do not expose the database
  administration interface or its credentials to an untrusted network.

## Authentication and users

The shared PostgreSQL schema is owned by Django models and migrations in the
`apps/users` and `apps/authentication` feature apps. Apply it with:

```shell
uv run python src/manage.py migrate
```

For Google sign-in, the client sends its Google ID token to
`POST /api/v1/auth/google/`. The backend validates the token audience against
`GOOGLE_CLIENT_ID`. For Firebase phone sign-in, the client completes Firebase's
SMS/OTP flow and sends the resulting Firebase ID token to
`POST /api/v1/auth/firebase/`. The backend validates it against
`FIREBASE_PROJECT_ID` using Firebase Application Default Credentials; in
deployment, provide credentials through `GOOGLE_APPLICATION_CREDENTIALS` or the
platform's workload identity. Do not commit provider credentials.

Both sign-in endpoints require `id_token` and `device_id`; `device_name`,
`platform`, and `app_version` are optional. The API returns a short-lived HIMA
bearer access token and a one-time opaque refresh token. Refresh tokens are
stored only as keyed hashes, rotated at `POST /api/v1/auth/refresh/`, and reuse
of an old token revokes its session. Revoke the current session with
`POST /api/v1/auth/logout/` and its bearer access token.

Authenticated user endpoints:

- `GET` / `PATCH /api/v1/users/me/` (name and username)
- `GET` / `PATCH /api/v1/users/me/profile/`
- `GET` / `PATCH /api/v1/users/me/preferences/`

The backend never receives the Firebase SMS code itself. The supplied
`auth_challenges` table remains for the email-OTP use case in the shared schema;
it is not used for Firebase phone verification.

Interactive API documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

Swagger documents the health check, Google and Firebase sign-in, refresh and
logout operations, and the authenticated user, profile, and preferences
endpoints. Use the **Authorize** control in Swagger UI to enter a HIMA access
token for endpoints marked as requiring bearer authentication.

API errors use the same JSON envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": {
      "id_token": ["This field is required."]
    }
  }
}
```

Validation errors include field-level `details`; other errors use `null`.
Unexpected server errors return a generic message, while diagnostic logs record
the request method/path, status, error code, and exception type without logging
request bodies or token values.

## Quality checks

The configured quality checks are:

```shell
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
uv run mypy src
uv run pytest
uv run coverage run -m pytest
uv run python src/manage.py check
uv run python src/manage.py spectacular --file /tmp/hima-openapi.yaml --validate
uv run bandit -c pyproject.toml -r src
uv run pip-audit
uv run pre-commit run --all-files
```

Install the hooks once per checkout:

```shell
uv run pre-commit install
```

## Architecture

Application code lives under `src/`. Persistence boundaries are represented by
interfaces in `apps/core/dao/interfaces.py`, with Django-backed implementations
in `apps/core/dao/impl.py`. API views depend on the interface rather than directly
on ORM details. The `apps/users` and `apps/authentication` feature apps follow the
linked practices guide's `services/interface/` and `services/impl/` structure.
Each service interface is a typed `Protocol`; the implementation is injected by
the view layer. Only layers used by a feature are present.
