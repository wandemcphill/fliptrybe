# FlipTrybe Mega Tasks (Phase 2.14) — Release Gate (Render + APK)

Date: 2026-02-04

This checklist is the “ship will not sink” gate. Every item here must be either **Done**, **Intentionally Deferred**, or **Removed** before production push.

## A) Messaging Trust Layer (SMS + WhatsApp) — Anti-Fraud
1. **Unify notification system**: choose ONE queue + ONE dispatcher module (retire duplicates under `app/segments/segment_*notification*`).
   - Action: standardize on `NotificationQueue` + `autopilot.process_notification_queue()` for SMS/WhatsApp.
   - Action: keep `notifications` table for in-app only.
   - Action: ensure `/api/admin/notifications/process` calls the real queue processor (no stubs).
2. **Delivery outcomes are stored**: every SMS/WhatsApp attempt must record `status`, `provider_message_id`, `provider_response`, `failed_reason`.
3. **Retry policy**: exponential backoff with max attempts; dead-letter queue for repeated failures.
4. **Templates (no free-text)**: OTP, payout notice, order event, inspector alert, KYC alert, dispute alert.
5. **Sender integrity**: ensure WhatsApp channel uses approved sender/number; block if not configured.
6. **Environment guard**: in production, block demo “send-any-message” endpoints and dev tools.

## B) Money Box + Wallet Ledger — No Double Credit, No Negative Balances
1. **Debit must fail on insufficient available funds** (available = balance - reserved). Never “floor to zero”.
2. **Idempotency everywhere**: topups, payouts, escrow releases, commission sweeps, inspector bond posts.
3. **Ledger is the source of truth**: balances computed or reconciled periodically; add a reconciliation job.
4. **Reserved funds invariant**: reserved cannot exceed balance; release cannot go below 0; all transitions logged.
5. **Audit trails**: wallet txns must include actor, reason, reference, and link to order/payout/inspection.
6. **Admin tooling**: read-only ledger explorer + anomaly flags (duplicate refs, large jumps, negative attempts).

## C) Roles + Access Control — Buyer / Merchant / Driver / Inspector / Admin
1. **Role gates on every endpoint**: backend rejects wrong role even if frontend leaks a button.
2. **Role gates on every screen**: frontend cannot route-push privileged screens without correct role.
3. **Visible Sign Out for every role shell** with nav-stack reset.
4. **Driver & Inspector onboarding mediated**: ensure no endpoint allows self-activation without admin workflow.
5. **Admin endpoints locked**: require admin token, add rate limits, and safe error messages.
6. **Remove weak admin heuristics**: never treat “admin@...” emails as admin; only `role==admin` or a single seeded superuser id.

## D) Listings Integrity — Demo Listings + Location Sweep
1. **Single canonical demo seed** endpoint; remove/disable duplicates.
2. **Location validation**: state/city/lga/locality are consistent; coords exist where required.
3. **Feed cards always navigate** to details (Declutter + Shortlets) even if purchase/booking is deferred.
4. **Detail pages render safely** if some fields are missing (no crashes, show “Not set”).
5. **Search/filter correctness**: no silent empty results; show empty-state reasons and retry on network error.

## E) Inspector System — Trust + Bonds + Reputation
1. **Bond lifecycle**: fund → reserve → deduct (penalties) → release → payout; all ledgered.
2. **Inspection jobs**: assignment rules, evidence capture hooks, timestamped events, status transitions.
3. **Fraud controls**: suspicious patterns trigger alerts (repeat disputes, frequent bond deductions, location mismatch).

## F) Deployment (Render) + Release (APK)
1. **BASE_URL config**: dev uses emulator (10.0.2.2); prod uses Render URL via `--dart-define`.
2. **Disable demo/dev endpoints in production** (seed, devtools, debug routes).
3. **Migrations**: ensure alembic/Flask-Migrate run on Render deploy.
4. **Logging**: structured logs for auth, wallet, payouts, notifications, inspections.
5. **Release checklist**: `flutter analyze`, release build, install on fresh device, smoke through sign-in + feeds + logout.

## G) Automated “Autopilot” (No Manual Admin Loops)
1. Notification dispatcher runs on schedule/worker (not only when endpoints are hit).
2. Payout runner + escrow runner are idempotent and safe to run repeatedly.
3. Daily reconciliation job: wallets + moneybox + payouts + escrow.

## H) Production Hygiene — Keep the Repo Clean
1. **Remove compiled artifacts**: delete committed `__pycache__/` and `*.pyc` files from the repo/zip.
2. **No secrets in source control**: replace `backend/.env` with `.env.example` (keep real secrets out of git).
3. **Disable create_all hooks** in production: avoid `db.create_all()` in request hooks; rely on migrations.
4. **Single source of config truth**: Render env vars drive DB/secret/cors; Flutter uses `--dart-define`.
5. **404 all dev helpers in prod**: role switch, demo seed, devtools.

## I) Observability + Incident Response — Fast Debug, Fast Rollback
1. **Correlation IDs**: include a request id in logs for auth, wallet, payouts, inspections.
2. **Notification outcomes dashboard**: queued/sent/failed counts + last failures.
3. **Wallet anomaly flags**: spike detection, repeated failures, duplicate idempotency attempts.
4. **Rollback checklist**: revert Render deploy + Flutter build version bump policy.

---
### Definition of Done
A task is “Done” only when:
- tested on emulator AND at least one fresh install
- tested against Render staging endpoint
- has a clear rollback strategy (or is isolated)
