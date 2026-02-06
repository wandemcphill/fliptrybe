# TASKLIST_ADDENDUM.md

## REQUIRED MODULES NOT YET BUILT – MUST IMPLEMENT

### 1) MARKETPLACE (complete)
- Listings CRUD by merchant
  - Acceptance: Merchant can create, edit, and delete listings via API; listing appears/updates in feed.
- Browse/search by buyer
  - Acceptance: Buyer can browse feed and search/filter by state/city/category/keyword.
- Listing detail view
  - Acceptance: Buyer can open listing detail and see price, seller, images, condition, location.
- Checkout/order creation
  - Acceptance: Buyer can create an order from a listing and receive order ID.
- Post-payment lifecycle
  - Acceptance: Payment success sets escrow to HELD and respects inspection rules.
- Buyer order history + timeline
  - Acceptance: Buyer can list past orders and view timeline entries.

### 2) MERCHANT DASHBOARD (complete)
- Listings management
  - Acceptance: Merchant can list, create, update, delete own listings.
- Orders queue (new / accepted / in-progress / completed / cancelled)
  - Acceptance: Merchant can view orders by status and accept/reject per role rules.
- Earnings summary
  - Acceptance: Merchant can view summary of released escrow amounts.
- Wallet balance + payout status
  - Acceptance: Merchant can view wallet balance and payout history.

### 3) DRIVER DASHBOARD (complete)
- Jobs queue
  - Acceptance: Driver can view assigned jobs.
- Accept/decline (if applicable)
  - Acceptance: Driver can accept assigned job or decline if allowed.
- Status updates (picked up / en route / delivered)
  - Acceptance: Driver can update status in sequence; completion locked by escrow.
- Earnings view
  - Acceptance: Driver can view earnings summary.

### 4) ADMIN PORTAL (complete)
- Users overview (buyers, merchants, drivers, inspectors)
  - Acceptance: Admin can list users by role.
- Listings and orders overview
  - Acceptance: Admin can list and inspect listings/orders.
- Payouts and wallet reconciliation
  - Acceptance: Admin can view payouts and wallet ledger.
- Dispute/override tools
  - Acceptance: Admin can adjudicate FAIL/FRAUD audits and update outcomes.
- Automation where possible (avoid manual loops)
  - Acceptance: Escrow runner and audits operate via scheduled jobs.

### 5) INSPECTOR MODULE (complete)
- Inspector role or permission
  - Acceptance: /api/auth/me returns role=inspector for inspector account.
- Inspection assignment or claim flow
  - Acceptance: Inspectors can be assigned or claim inspections.
- Check-in states: on my way / arrived
  - Acceptance: State machine enforced; no skipping states.
- Evidence requirement for fail/fraud (photo/video + note)
  - Acceptance: FAIL/FRAUD without evidence returns 409.
- Outcomes: passed / failed / fraud
  - Acceptance: Outcomes set and recorded correctly.
- Impact on order: proceed / refund / hold / dispute
  - Acceptance: PASS releases escrow when required; FAIL/FRAUD refunds; disputes logged.
- Support inspection for already-paid orders
  - Acceptance: Retroactive inspection can be requested for paid orders.

### 6) SHORTLET MODULE (complete)
- Shortlet listings
  - Acceptance: Shortlets list and detail endpoints return data.
- Availability rules
  - Acceptance: Booking respects availability and date conflicts.
- Booking lifecycle
  - Acceptance: Create, confirm, and cancel bookings with proper status updates.
- Payment/hold logic
  - Acceptance: Booking payments follow escrow/hold rules.
- Cancellation rules
  - Acceptance: Cancellations update wallet/ledger appropriately.
- Wallet/ledger integration
  - Acceptance: Ledger entries created for booking transactions.

### 7) WALLETS & LEDGER (complete)
- Wallet per user
  - Acceptance: Every user has a wallet record.
- Immutable ledger entries
  - Acceptance: Ledger entries are append-only.
- Reserved/held balances
  - Acceptance: Holds/reserves recorded and released correctly.
- Release on completion
  - Acceptance: Release occurs only when escrow released.
- Refunds on cancel/fail
  - Acceptance: Refunds created for cancelled/fail outcomes.
- Merchant/driver payouts
  - Acceptance: Payouts only when escrow released.
- Reconciliation safeguards (no negative or double spend)
  - Acceptance: Balance never negative; idempotent ledger postings.

### 8) LANDING PAGE
- App entry point
  - Acceptance: Landing page is first screen and routes to login/signup.
- Role-aware routing
  - Acceptance: After login, user is routed to correct dashboard by role.
