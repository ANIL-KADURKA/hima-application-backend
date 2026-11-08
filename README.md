# HIMA application backend

Typed Django REST Framework backend managed with [`uv`](https://docs.astral.sh/uv/).

## Setup

Install `uv`, then create the environment and install application plus development
dependencies:

```shell
uv sync
cp .env.example .env
uv run python src/manage.py migrate
uv run python src/manage.py runserver
```

The health endpoint is available at `GET /api/v1/health/`.

Interactive API documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

## Quality checks

This repository intentionally contains no test files yet. The configured commands
still run successfully against an empty test suite:

```shell
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
uv run mypy src
uv run pytest
uv run coverage run -m pytest
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
on ORM details.
