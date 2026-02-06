# FlipTrybe Backend Deploy (Render)

## Required env vars
- `FLIPTRYBE_ENV=production`
- `SECRET_KEY` (min 16 chars)
- `DATABASE_URL` (Render Postgres URL)
- `CORS_ORIGINS` (comma-separated, e.g. `https://your-frontend.com`)
- `FLIPTRYBE_ENABLE_DEMO_SEED` set to `1` only if you explicitly want `/api/demo/seed` enabled in prod

## Optional env vars
- `FLIPTRYBE_ENABLE_DEMO_SEED=1` to allow demo seed in production
- `FLIPTRYBE_SEED_RESET=1` to allow reset behavior when seed runs
- `FLASK_HOST` and `FLASK_PORT` (for local only; Render ignores)

## Render build and start
- Build command: `pip install -r requirements.txt`
- Start command: `python main.py`

## Migrations
- Run on deploy (Render shell or build step):
  - `python -m flask db upgrade`
- The app fails fast if `DATABASE_URL` is missing in production.

## Verify after deploy
1) Health:
- `GET /api/health` -> `ok:true` and `db:ok`

2) Version:
- `GET /api/version` -> `ok:true`, `alembic_head`, `git_sha`

3) Auth sanity:
- `POST /api/auth/login` with a known admin user
- `GET /api/auth/me` with returned token

4) Order flow sanity:
- Create an order (`POST /api/orders`) with a new `payment_reference`
- Confirm availability (if enabled by the flow)
- Ensure status transitions and timeline are present

## Notes
- This backend never uses `fliptrybe-logistics`; SQLite is pinned to `backend/instance/fliptrybe.db` in dev.
- `/api/demo/seed` is blocked in production unless `FLIPTRYBE_ENABLE_DEMO_SEED=1`.
