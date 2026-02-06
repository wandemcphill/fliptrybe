# Success Criteria (Codex Acceptance Tests)

## Invariants (must always hold)
- No DELIVERED/COMPLETED while escrow_status = HELD.
- No seller payout while escrow_status != RELEASED.
- If inspection_required=true then escrow release requires inspection_outcome=PASS.
- FAIL/FRAUD requires evidence_urls + note.

## Queries that must always return 0
(Use table/column names as implemented)

- Orders completed while held escrow.
- Payout records created for held escrow.

## Manual test scripts
1) Create order -> mark paid -> verify escrow HELD.
2) Request inspection -> progress states with correct ordering.
3) PASS -> run escrow runner -> verify RELEASED.
4) FAIL with evidence -> run escrow runner -> verify REFUNDED.
5) Attempt complete while HELD -> expect 409.
