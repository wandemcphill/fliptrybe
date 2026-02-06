# Codex Implementation Lock: Escrow Automation + Inspector Reputation

This repo includes **Inspector Agent Mode** tied to **Escrow primitives**, plus an initial **Inspector Reputation** system.

## What was implemented in this update

### Backend models

1. `orders` table (model: `backend/app/models/order.py`)
   - Added escrow fields:
     - `escrow_status` (NONE|HELD|RELEASED|REFUNDED|DISPUTED)
     - `escrow_hold_amount`, `escrow_currency`
     - `escrow_held_at`, `escrow_release_at`, `escrow_refund_at`, `escrow_disputed_at`
     - `release_condition` (INSPECTION_PASS|BUYER_CONFIRM|TIMEOUT|ADMIN)
     - `release_timeout_hours`
   - Added inspection fields:
     - `inspection_required` (bool)
     - `inspection_status` (NONE|PENDING|ON_MY_WAY|ARRIVED|INSPECTED|CLOSED)
     - `inspection_outcome` (NONE|PASS|FAIL|FRAUD)
     - `inspector_id`
     - timestamps: `inspection_requested_at`, `inspection_on_my_way_at`, `inspection_arrived_at`, `inspection_inspected_at`, `inspection_closed_at`
     - `inspection_evidence_urls` (JSON string of URLs), `inspection_note`

2. New tables (model file: `backend/app/models/inspection_reputation.py`)
   - `inspector_profiles`
   - `inspection_reviews`
   - `inspection_audits`

### Backend endpoints

File: `backend/app/segments/segment_inspections_api.py`

- Buyer requests inspection (retroactive allowed)
  - `POST /api/orders/{order_id}/inspection/request`

- Inspector strict timeline status (NO SKIP)
  - `POST /api/inspections/{order_id}/status` body: `{ "status": "ON_MY_WAY"|"ARRIVED"|"INSPECTED" }`

- Inspector outcome submission
  - `POST /api/inspections/{order_id}/outcome` body:
    - `{ "outcome": "PASS"|"FAIL"|"FRAUD", "evidence_urls": ["..."], "note": "..." }`
    - Evidence + note are REQUIRED for FAIL/FRAUD.

- Buyer review
  - `POST /api/inspections/{order_id}/review` body:
    - `{ "rating": 1-5, "tags": ["punctual"], "comment": "..." }`

- Admin audit/adjudication
  - `POST /api/inspections/{order_id}/audit` body:
    - `{ "decision": "UPHELD"|"OVERTURNED", "reason": "..." }`

- Inspector self profile (auto-provision)
  - `GET /api/inspectors/me/profile`

- Run escrow automation (admin)
  - `POST /api/admin/escrow/run` body: `{ "limit": 500 }`

### Escrow automation runner

File: `backend/app/jobs/escrow_runner.py`

- `run_escrow_automation(limit=...)` releases/refunds based on inspection outcome.

## Migration / DB notes

This repo uses SQLAlchemy + Flask-Migrate. Run the following after pulling the update:

```bash
cd backend
flask db init  # only if migrations/ doesn't exist yet
flask db migrate -m "escrow + inspection + inspector reputation"
flask db upgrade
```

If you are using SQLite locally and prefer no Alembic, you can delete the DB and let `db.create_all()` recreate tables.

## Remaining work for Codex (recommended)

1. Wire escrow HOLD on payment success
   - When payment provider confirms payment, set:
     - `order.escrow_status = HELD`
     - `order.escrow_held_at = now`
     - `order.escrow_hold_amount = amount + delivery_fee`

2. Improve inspector assignment
   - Use city/region matching from user profile or listing location.
   - Add load-balancing (active jobs count).

3. Add Flutter screens
   - Buyer: Request inspection from order history + see inspector status timeline.
   - Inspector: On my way / Arrived / Inspected buttons + outcome form + evidence upload.
   - Buyer: Rate inspector after CLOSED.
