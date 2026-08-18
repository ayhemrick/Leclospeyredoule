# Clos Peyredoule — API

FastAPI service backing the visitor site: public content, the guest guide
gated behind a rotating QR code, and the admin section.

## Layout

| Path            | Contents                                                      |
| --------------- | ------------------------------------------------------------- |
| `app/core`      | settings, logging, cookies, password and token primitives      |
| `app/db`        | declarative base, async engine and session                     |
| `app/models`    | ORM tables                                                     |
| `app/schemas`   | Pydantic request and response models                           |
| `app/services`  | access control, auth, auditing, QR rendering, seeding          |
| `app/api/v1`    | routers                                                        |
| `alembic`       | migrations                                                     |
| `tests`         | pytest suite (needs a live Postgres)                           |

## Local commands

Dependencies are managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                    # create .venv from uv.lock
uv run alembic upgrade head                # apply migrations
uv run uvicorn app.main:app --reload       # serve on :8000
uv run ruff check . && uv run ruff format --check .
uv run mypy app
uv run pytest
```

`DATABASE_URL` and `APP_SECRET_KEY` must be set; the repository root
`.env.example` documents every variable.

## Access-control model

* One `access_code` row is active at a time; it is what the printed QR encodes.
* `POST /api/v1/access/redeem` swaps that code for an opaque token, returned as
  an `HttpOnly` cookie and stored only as an HMAC.
* Rotation cadence and guest session length live in `access_policy`, editable
  by an owner in the admin section. Rotation happens in a background worker and
  lazily on request, so an idle deployment still rotates.
* Administrators sign in with Argon2id passwords and carry short-lived JWT
  cookies plus a double-submit CSRF token.
