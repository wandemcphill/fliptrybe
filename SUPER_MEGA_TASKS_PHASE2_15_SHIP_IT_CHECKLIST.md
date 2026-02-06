# SUPER MEGA TASKS — Phase 2.15 “Ship-It” Checklist (Render + APK)

This is the **hard gate** checklist to ensure FlipTrybe does not ship with trust holes, broken flows, or accounting exploits.

---

## A) Fraud + Trust Messaging (SMS/WhatsApp) — MUST PASS
1. **Single outbound channel service**
   - One canonical sender (Termii client), used by: OTP, order events, escrow events, payout events, inspector events.
   - Remove/retire any “fake send” paths that mark messages delivered without actually sending.

2. **Queue reliability**
   - Notification queue must record:
     - provider response (status/message/id)
     - attempt_count
     - last_attempt_at
     - next_retry_at (exponential backoff)
     - final_state: queued/sent/failed/dead-letter

3. **Fraud combat templates**
   - Create template set with immutable message IDs:
     - OTP login / OTP reset
     - “Order created”
     - “Escrow funded / held”
     - “Inspection assigned”
     - “Inspection completed”
     - “Payout initiated / completed”
     - “Suspicious activity alert” (rate-limit + lock)
   - Templates must be short, consistent, and unspoofable (no “click here” links unless from verified domain).

4. **WhatsApp parity**
   - WhatsApp messages must be sent for the same critical events as SMS (configurable toggles).
   - If WhatsApp fails, SMS is attempted (fallback) and logged.

---

## B) MoneyBox + Wallets + Ledger Invariants — MUST PASS
1. **Ledger is source of truth**
   - Wallet.balance must always equal sum(ledger credits - debits) unless using a strict cached field with reconciliation.

2. **Reserved funds are untouchable**
   - All debits must check **available = balance - reserved**.
   - No “clamp to zero” on debit failures. Fail hard with a clear error.

3. **Idempotency**
   - Every wallet mutation endpoint must accept an idempotency key and enforce uniqueness:
     - topups
     - escrow holds
     - refunds
     - payouts
     - slashes / fees
   - Replay must return the original result.

4. **Reconciliation job (Phase 2.15)**
   - Add nightly job:
     - recompute balances from ledger
     - detect anomalies: negative reserved, available < 0, balance mismatch
     - flag accounts in `account_flags` and notify admin.

5. **Audit trails**
   - Every movement records: actor_user_id, reference_type, reference_id, request_id.

---

## C) Role & Access Control — MUST PASS
1. **Role-based UI + API lock**
   - Buyer cannot access merchant/driver/admin endpoints by guessing routes.
   - Driver registration remains mediated; inspector access must be explicitly role-gated.

2. **Admin hardening**
   - Admin only by role, never by email heuristic.
   - Ensure admin-only endpoints require token + role check.

---

## D) Inspector System — MUST PASS
1. **Bond lifecycle**
   - Required bond by tier enforced server-side.
   - Reserve/release/slash flows idempotent per (reference_type, reference_id).
   - Bond reserved + available cannot go negative.

2. **Inspection assignment rules**
   - Only inspectors with ACTIVE bond can accept.
   - Assignment must be atomic (no double-accept race).
   - SLA timers: late acceptance, late completion.

3. **Inspector reputation**
   - Reputation updates only from completed inspections.
   - Fraud flags reduce reputation and can trigger bond increase requirement.

---

## E) Listings Integrity + Location Sweep — MUST PASS
1. **Single Nigeria locations dataset**
   - All demo and production validation uses `app/utils/ng_locations.py`.

2. **Location validation**
   - State and city must be valid pair; if invalid, fallback to:
     - state valid city, or
     - “Location not set” (frontend)
   - Coordinates resolved via `get_city_coords(city)` when available.

3. **Demo listings**
   - Demo seed must produce:
     - non-empty listings in each category
     - stable IDs and idempotent behavior (no duplicates)
     - correct state/city values for Lagos and Abuja at minimum

---

## F) Frontend Release Readiness (APK) — MUST PASS
1. **Environment base URL**
   - Release build MUST NOT point to 10.0.2.2.
   - Use `--dart-define=BASE_URL=...` or config file switching.

2. **Navigation integrity**
   - Every listing card navigates to a detail screen.
   - Every role has visible logout and nav stack reset.

3. **Failure UX**
   - 401 forces re-login and clears token.
   - Empty states and network errors show retry.

---

## G) Render Deployment Safety — MUST PASS
1. **Disable demo endpoints in prod**
   - `/api/demo/*` blocked when `FLIPTRYBE_ENV=prod`.

2. **Secrets**
   - No `.env` committed; use Render env vars.
   - SECRET_KEY must be set in Render.

3. **Migration discipline**
   - Apply migrations on deploy.
   - No `db.create_all()` in production startup paths.

---

## H) Super Mega “Pre-Launch” Test Script — MUST PASS
Run and record:
1. Buyer register + login + logout
2. Listings feed load + open detail + back
3. Create order from listing (if present) and verify events timeline non-empty
4. Wallet debit fails when insufficient available funds
5. Notification queue: enqueue + process + sent/failed recorded
6. Inspector bond: topup + reserve + release + slash idempotency checks


## SUPER MEGA TASKS (Signup + Trust UX)
- [ ] Role-first onboarding: Landing -> Role selection -> tailored signup (Buyer/Driver/Merchant/Inspector) with clear value props.
- [ ] Driver + Inspector signup are **admin-mediated** but still create a base account and a pending request (no more dead-end 410).
- [ ] Merchant pitch: highlight remote earning (global merchants can sell listings for clients across Nigeria) + commissions + MoneyBox interest.
- [ ] Landing “Live Confirmations” board: public, non-PII ticker from recent paid events (mask identities; show title + location + amount).

## SUPER MEGA TASKS (MoneyBox Tier Wiring)
- [ ] Verify tier lock_days and bonus_rate map 1:30d, 2:120d, 3:210d, 4:330d are reflected in frontend tiers UI.
- [ ] Ensure penalty rates apply exactly to early withdrawals and are recorded to ledger.
- [ ] Ensure bonus awards occur only once at maturity, are idempotent, and are visible in ledger + balances.
- [ ] Autosave from commission kinds: confirm each commission credit path calls autosave_from_commission with stable reference idempotency.

## SUPER MEGA TASKS (Notifications Reliability)
- [ ] Retry/backoff fields on notification queue (attempt_count, next_attempt_at, dead-letter) and admin UI visibility for dead-lettered failures.
- [ ] Add operator tooling: endpoint to requeue dead-lettered messages after fixing provider outage.

## SUPER MEGA TASKS (Wallet Integrity)
- [ ] Nightly wallet reconciliation job logs anomalies (ledger vs stored balance, reserved exceeds balance).
- [ ] Add admin dashboard endpoint to review anomalies and reconcile decisions.


## Super Mega Add-ons (Audit Closure)
- Merchant follow wiring: buyer/seller can follow merchants; merchants cannot follow anyone; ensure follow count & status endpoints are used in UI.
- Support-only chat: no user-to-user messaging; everyone can message admin; admin can reply to any user.
- Delivery secret codes: pickup + dropoff code generation, distribution via SMS/WhatsApp, 4-attempt lockout, and admin escalation path.
- Self-buy prevention: block sellers from purchasing their own listings at API level (even if UI tries).
