# FlipTrybe Handover to Codex (Execution Brief)

Owner: Omotunde Oni  
Handover date: 2026-02-02  
Timezone: Europe/Athens

This repository is the **authoritative source of truth** for FlipTrybe. Codex must behave like a senior engineer executing a locked product spec.

## Mission
1) Build an **APK-ready Android app** from `frontend/` (Flutter).  
2) Deploy the **backend API** from `backend/` (Flask + SQLAlchemy) to production (Render recommended).  
3) Finish remaining wiring so the platform is **fully automated, synchronized, and loophole-free**.  
4) Do **not** weaken or “reinterpret” product rules. If anything is unclear, prefer the strictest enforcement.

---

## Repo layout (do not restructure)
- `frontend/` Flutter mobile app (Android build target)
- `backend/` Flask API server
- `tools/` build scripts
- `CODEX_APK_RUNBOOK.md` APK run/build steps
- `CODEX_NEXT_UPGRADES.md` remaining engineering tasks (already in repo)
- `HANDOVER_TO_CODEX.md` (this file)

---

## Product Vision Lock (Non-negotiable)

### A) Marketplace reality
FlipTrybe is a marketplace where buyers purchase items from other users/merchants/agents.

### B) The trust gap we are closing
High-risk items (cars, phones, TVs, consoles, etc.) must support **post-payment authenticity verification** via an **Item Inspector Agent**.

### C) Inspector Agent Mode (strict, no-skip state machine)
Inspection must follow this timeline (no skipping):
`PENDING -> ON_MY_WAY -> ARRIVED -> INSPECTED`

Inspection outcome must be exactly one:
- `PASS`
- `FAIL`
- `FRAUD`

Evidence rule (hard enforcement):
- If outcome is `FAIL` or `FRAUD`, inspector MUST submit:
  - at least **1 photo/video URL**
  - a **short note**
- Without evidence+note: return HTTP 409 (or 422) and do not change state.

Retroactive inspection:
- Inspection can be requested for already-paid orders from watchlist/history.

### D) Escrow automation (no loopholes)
Funds must remain **HELD** until release conditions are satisfied.

**NO-LOOPHOLE RULE (absolute):**
> An order can NEVER be marked DELIVERED / COMPLETED while `escrow_status = HELD`.

Release/refund rules:
- If inspection required:
  - `PASS` can release escrow (subject to `release_condition`)
  - `FAIL/FRAUD` triggers refund
- Admin is **autopilot** for normal transitions (no manual approve/reject for standard escrow flows).

### E) Inspector reputation scoring
Inspectors have profiles and reputation driven by:
- Reviews (ratings)
- Audits (upheld/overturned)
- Timeliness
Reputation influences assignment priority and eligibility for high-risk categories.

### F) Inspector insurance/bonding
Bonding adds economic accountability:
- Inspectors must maintain a bond balance.
- Assignment reserves a portion of bond.
- If an audit overturns an inspector FAIL/FRAUD decision, bond can be slashed.
This must be implemented as specified below (Section 9).

---

## What is already implemented in code (confirmed present)
Backend already includes:
- Escrow fields on orders (status/amount/timestamps/release_condition/timeout)
- Inspection gate fields on orders (inspection_required/status/outcome/timeline/evidence/note/inspector_id)
- Inspector reputation tables:
  - `inspector_profiles`
  - `inspection_reviews`
  - `inspection_audits`
- Strict inspection endpoints (state machine + evidence enforcement)
- Escrow runner job: `backend/app/jobs/escrow_runner.py`
- Admin trigger endpoint to run escrow runner

Your job is to wire remaining production-grade connections and ship.

---

## Build targets

### Target 1: APK
Deliver:
- `app-release.apk`
- (recommended) `app-release.aab`

### Target 2: Production
- Backend deployed with Postgres
- Migrations applied
- Escrow runner scheduled
- No-loophole invariants enforced on server

---

## Exact commands Codex must run

### Backend (local)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env

# Migrations
flask db init || true
flask db migrate -m "escrow + inspections + inspector reputation + bonding"
flask db upgrade

python main.py
# or: gunicorn -b 0.0.0.0:5000 "app:create_app()"
```

### Flutter (local)
```bash
cd frontend
flutter doctor
flutter pub get
flutter run
```

### Build APK (fast)
Linux/macOS:
```bash
./tools/build_apk.sh
```
Windows PowerShell:
```powershell
.\\tools\\build_apk.ps1
```

### Release signing (Codex must NOT invent secrets)
Create keystore:
```bash
keytool -genkeypair -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

Create `frontend/android/key.properties` with user-provided secrets:
```properties
storePassword=YOUR_STORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=upload
storeFile=upload-keystore.jks
```

Build:
```bash
cd frontend
flutter build apk --release
flutter build appbundle --release
```

---

## Production deploy (Render)

### Start command
```bash
gunicorn -b 0.0.0.0:$PORT "app:create_app()"
```

### Minimum env vars
- `SECRET_KEY`
- `DATABASE_URL` (Postgres)
- `FLASK_ENV=production`
- `CORS_ORIGINS`
- Payment provider keys (if enabled)

### Migration step (must run)
```bash
flask db upgrade
```

---

## Mandatory “no-loophole” invariants (Codex must enforce)
These must be enforced **server-side** (UI is not security):

1) **Completion Lock**
- If `escrow_status == HELD` → reject any attempt to set order `DELIVERED/COMPLETED/CLOSED` (HTTP 409).

2) **Payout Lock**
- If `escrow_status != RELEASED` → do not pay seller, do not create payout.

3) **Inspection Lock**
- If `inspection_required == true` and `inspection_outcome != PASS` → escrow cannot be released.

4) **Evidence Lock**
- If `inspection_outcome in (FAIL, FRAUD)` and evidence+note missing → reject outcome submission.

5) **Runner Consistency**
- Escrow runner should detect illegal combos (COMPLETED while HELD) and:
  - revert to safe state or mark DISPUTED
  - log an audit entry

---

## Mandatory remaining wiring (finish these)

### 1) Payment success must HOLD escrow (non-negotiable)
Wherever payment success is confirmed (webhook/client confirm), set:
- `escrow_status = HELD`
- `escrow_hold_amount = paid_amount`
- `escrow_held_at = now()`
- for inspection-required orders:
  - `release_condition = INSPECTION_PASS`

### 2) Schedule escrow runner
Must execute every 2–5 minutes.

Preferred: Render Cron Job hitting:
- `POST /api/admin/escrow/run`

Example:
```bash
curl -X POST https://YOUR_BACKEND/api/admin/escrow/run -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### 3) Evidence storage policy
Ensure inspection evidence URLs come from a storage provider:
- Local dev: filesystem ok
- Production: S3 or Supabase Storage (recommended)
Use signed URLs if needed.

---

## Inspector insurance / bonding (implement exactly)

### Tables to add
Create:
- `inspector_bonds`
- `bond_events`

**inspector_bonds**
- `id`
- `inspector_user_id` (unique)
- `bond_currency`
- `bond_required_amount`
- `bond_available_amount`
- `bond_reserved_amount`
- `status`: `ACTIVE | SUSPENDED | UNDERFUNDED`
- `last_topup_at`, `last_slash_at`
- timestamps

**bond_events**
- `id`
- `inspector_user_id`
- `event_type`: `TOPUP | RESERVE | RELEASE | SLASH | REFUND_SUPPORT`
- `amount`
- `reference_type`: `INSPECTION | AUDIT | ORDER`
- `reference_id`
- `note`
- `created_at`

### Bond rules
- Assignment gate: cannot assign if `bond_available_amount < bond_required_amount`.
- Reserve on assignment: move amount from available → reserved (log event).
- Release on PASS completion without dispute: reserved → available (log event).
- Slash on audit OVERTURNED for FAIL/FRAUD: reduce reserved/available (log event).
- Auto-suspend when underfunded: `status=UNDERFUNDED` and block assignment.

### Integration points
- On inspector assignment: reserve bond.
- On inspection closure (PASS): release reserve (if no dispute).
- On audit OVERTURNED: slash bond.
- Tie bond requirements to reputation tier (higher tier → lower bond requirement).

---

## Definition of Done (DoD)

### APK
- `flutter build apk --release` succeeds.
- Output exists:
  - `frontend/build/app/outputs/flutter-apk/app-release.apk`

### Backend
- Deployed to production and reachable.
- Postgres migrations applied.
- Escrow runner scheduled and executing.

### Flow tests (must pass)
1) Pay → escrow HELD → inspection requested → PASS → escrow RELEASED → order can complete.
2) Pay → escrow HELD → FAIL/FRAUD with evidence → auto REFUND → order cannot complete.
3) Attempt to mark complete while HELD → HTTP 409.
4) Underfunded inspector cannot be assigned.
5) Overturned audit slashes bond and logs bond_event.

---

## Deliverables Codex must output
- Signed `app-release.apk` (or unsigned release if secrets not provided)
- `app-release.aab` (recommended)
- Backend production URL
- Migration files committed/generated
- Short changelog of all edits and where to find them
