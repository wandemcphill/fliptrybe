# Codex PM Tasklist (Do Not Skip)

This is the step-by-step execution plan. Treat each checkbox as mandatory.

## A) Sanity check repo
- [ ] Do NOT move folders. Repo root must contain: `frontend/`, `backend/`, `tools/`.
- [ ] Confirm Flutter SDK installed and `flutter doctor` passes.
- [ ] Confirm Python 3.11+ available.

## B) Backend local boot
- [ ] Create venv, install requirements.
- [ ] Copy `.env.example` -> `.env`.
- [ ] Run migrations (`flask db migrate`, `flask db upgrade`).
- [ ] Start API locally and verify health endpoint(s).

## C) Flutter local boot
- [ ] `flutter pub get`.
- [ ] `flutter run`.
- [ ] Confirm app can reach backend base URL.

## D) Escrow wiring (must be done before production)
- [ ] On payment success, set `escrow_status=HELD` and `escrow_hold_amount`.
- [ ] Enforce server-side completion lock: cannot complete while HELD.
- [ ] Enforce server-side payout lock: cannot pay seller unless RELEASED.

## E) Escrow runner automation
- [ ] Ensure `backend/app/jobs/escrow_runner.py` is invoked via scheduler.
- [ ] Create a Render Cron job (or equivalent) calling `POST /api/admin/escrow/run` every 2–5 minutes.

## F) Inspector system
- [ ] Verify strict inspection state machine: `PENDING->ON_MY_WAY->ARRIVED->INSPECTED`.
- [ ] Verify FAIL/FRAUD evidence+note required.
- [ ] Verify reputation tables update via reviews/audits.

## G) Inspector insurance / bonding (implement)
- [ ] Add tables `inspector_bonds` and `bond_events`.
- [ ] Block inspector assignment if bond underfunded.
- [ ] Reserve bond on assignment.
- [ ] Release reserve on PASS completion.
- [ ] Slash bond on audit OVERTURNED for FAIL/FRAUD.
- [ ] Auto-suspend underfunded inspectors.

## H) Production deployment (Render)
- [ ] Provision Postgres.
- [ ] Set env vars.
- [ ] Run `flask db upgrade`.
- [ ] Start with gunicorn.
- [ ] Confirm cron runner executes.

## I) APK deliverables
- [ ] Build unsigned release APK at minimum.
- [ ] If secrets provided, build signed `app-release.apk`.
- [ ] Build `app-release.aab` recommended.

## J) Final acceptance tests (must pass)
- [ ] Pay → HELD → PASS → RELEASED → order can complete.
- [ ] Pay → HELD → FAIL/FRAUD (evidence) → REFUNDED → cannot complete.
- [ ] Attempt to complete while HELD → HTTP 409.
- [ ] Underfunded inspector cannot be assigned.
- [ ] Overturned audit triggers bond slash and logs event.
