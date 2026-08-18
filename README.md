# Clos Peyredoule

A visitor site for a country house near **Blaye**, on the right bank of the
Gironde estuary: a public flyer about the property and the region, plus a guest
guide that unlocks only for people who scan the QR code posted inside the house.

> **This is a demonstration project.** The house, its history and its practical
> details are invented. Everything about the region — Vauban's citadel and its
> UNESCO listing, the estuary, the appellations, the museums — is real, and the
> photographs are openly licensed pictures of the area, never of the property.

| Layer    | Stack                                                                       |
| -------- | --------------------------------------------------------------------------- |
| Frontend | React 19 · Vite 8 · TypeScript 5.9 · Tailwind 4 · TanStack Router and Query  |
| Backend  | Python 3.14 · FastAPI · SQLAlchemy 2 (async) · Alembic · Pydantic 2          |
| Database | PostgreSQL 18                                                               |
| Quality  | ruff · mypy (strict) · pytest · ESLint 10 · Prettier · Vitest 4 · Playwright |

---

## What it does

**For a visitor.** The public site presents the house and a curated list of what
to do nearby, in French and English, switchable without a page reload.

**For a guest.** A QR poster hangs in the entrance hall. Scanning it opens
`/a/<code>`, which exchanges the code for a time-limited session and drops the
visitor straight into the guest guide: arrival and keys, Wi-Fi, heating, waste,
house rules, and the owner's addresses. The code is then removed from the URL,
so it does not linger in browser history or in the next guest's screenshot.

**For the owner.** An admin section manages the access rules, the code itself,
live sessions, the bilingual content, other administrators, and an audit log of
everything that was changed.

---

## Running it

Everything runs in Docker Compose. You need Docker with the Compose plugin;
nothing else has to be installed.

```bash
cp .env.example .env
```

Set at least `APP_SECRET_KEY` and `ADMIN_PASSWORD` in `.env`. A good secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Then:

```bash
docker compose up --build
```

| Service     | URL                        |
| ----------- | -------------------------- |
| Site        | http://localhost:5173      |
| API         | http://localhost:8000      |
| API docs    | http://localhost:8000/docs |
| Admin       | http://localhost:5173/admin |

Sign in with the `ADMIN_EMAIL` and `ADMIN_PASSWORD` from your `.env`. The
database is migrated and seeded on first start: an owner account, an access
policy, the first code, and the demo content.

> **Ports already in use?** `API_PORT`, `WEB_PORT` and `POSTGRES_PORT` in `.env`
> move the host side of each mapping.

### Trying the QR flow

1. Sign in at `/admin`, open **Access & QR**.
2. The poster page shows the code, its scan URL and a printable QR.
3. Open the scan URL in a private window (or scan the QR with a phone on the
   same network, after setting `PUBLIC_BASE_URL` to your machine's LAN address).
4. The guest guide opens, with a countdown of the remaining window.
5. Press **Change the code now**: the old URL stops working immediately.

### Running without Docker

The API needs Python 3.14 (uv installs it) and a reachable PostgreSQL 18:

```bash
cd backend && uv sync && uv run alembic upgrade head && uv run uvicorn app.main:app --reload
```

```bash
cd frontend && npm ci && npm run dev
```

---

## How access control works

There is no visitor account, no e-mail, no password. The property has **one
active code at a time**, and that code is what the poster carries.

```
 poster  ──scan──▶  /a/<code>  ──POST /access/redeem──▶  guest_session
                                                              │
                              HttpOnly cookie ◀───────────────┘
                                     │
                              gated endpoints
```

- The cookie holds an opaque 256-bit token. Only its HMAC is stored, so a
  database dump cannot be replayed against the site.
- How long one scan grants access, and how often the code rotates, are owner
  settings (`access_policy`), editable in the admin section without a redeploy.
- Rotation happens both in a background worker and lazily on the next request
  that needs the code, so an idle deployment still rotates.
- Guests admitted by an older code keep their access until it lapses. That is
  deliberate — reprinting a poster should not lock out someone already in the
  house — and `revoke_sessions_on_rotation` turns it off for owners who disagree.
- A capacity cap (`max_active_sessions`) is available for properties that want
  a hard ceiling on concurrent guests.

Administrators are a separate system: Argon2id passwords following the OWASP
parameters, short-lived JWTs in `HttpOnly` cookies with a rotating refresh
token, a double-submit CSRF token on every mutation, per-account lockout after
repeated failures, and an owner/editor split — an editor can change content but
not the access policy or other accounts.

### A deployment trap worth knowing

The session cookie is `SameSite=Lax`. **The API must be same-site with the web
app**, or the browser silently drops it and the guide never unlocks. Serving the
site at `localhost:5173` with the API at `localhost:8000` is fine; `localhost`
for one and `127.0.0.1` for the other is not. In production, put both behind one
domain (for example `example.fr` and `example.fr/api`), or set `COOKIE_DOMAIN`
to the shared parent domain.

---

## Layout

```
backend/           FastAPI service
  app/core/        settings, logging, cookies, password and token primitives
  app/models/      ORM tables
  app/services/    access control, auth, auditing, QR rendering, seeding
  app/api/v1/      routers
  alembic/         migrations
  tests/           pytest suite (needs a live Postgres)
frontend/          React site
  src/routes/      public pages, the scan landing page, the admin section
  src/lib/         API client, query hooks, formatting
  src/i18n/        message catalogue and locale provider
  e2e/             Playwright specs
```

---

## Quality gates

```bash
make lint      # ruff, mypy --strict, ESLint, tsc
make test      # pytest + vitest
make e2e       # Playwright, against a running stack
```

CI runs the same checks on every push and pull request, plus a migration drift
check (`alembic check`), container builds and a Trivy scan of the API image.

The backend suite runs against a real PostgreSQL instance rather than SQLite,
because the schema depends on JSONB, generated UUIDs and row locking; each test
runs inside a transaction that is rolled back afterwards.

Optional but recommended:

```bash
pre-commit install
```

---

## Content and images

Demo content is seeded from `backend/app/services/seed_data.py` and is
**idempotent**: rows are inserted only when their slug is missing, so anything
the owner edits in the admin survives a redeploy. Set `SEED_DEMO_CONTENT=false`
to start with an empty site.

Photographs come from Wikimedia Commons under CC BY or CC BY-SA. Author, licence
and source are recorded in [`frontend/public/images/ATTRIBUTIONS.md`](frontend/public/images/ATTRIBUTIONS.md)
and shown in the app at `/credits`. Replacing them with photographs of a real
property means dropping files into `frontend/public/images` and updating both.

---

## Before this goes anywhere real

- Set a strong `APP_SECRET_KEY` and change `ADMIN_PASSWORD`; the API refuses to
  start in `APP_ENV=production` with the documented defaults still in place.
- Serve over HTTPS and set `COOKIE_SECURE=true`.
- Put the API behind a reverse proxy that sets `X-Forwarded-For`; client
  addresses are only ever stored as truncated keyed hashes.
- Back up the database — the audit log is only as durable as the volume.
- Login rate limiting is per account and held in the database; a multi-instance
  deployment behind a load balancer should add an IP-level limit at the edge.

---

## Licence

MIT — see [LICENSE](LICENSE). The photographs keep their own licences.
