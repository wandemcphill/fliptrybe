# Codex Readiness Score (2026-02-02)

## APK readiness: 85%
**Why:** Flutter project structure is present, Android tooling exists, build scripts and runbook exist.

**Remaining to reach 100% for Play Store release:**
- Release keystore + `key.properties` management
- Versioning discipline (versionCode/versionName)
- Optional: CI job for signed builds

## Production readiness: 60%
**Why:** Escrow/inspection/reputation primitives exist and the escrow runner exists, but prod wiring needs completion.

**Remaining to reach 90%+ (prod-grade):**
- Wire payment success to escrow HOLD (no exceptions)
- Schedule escrow runner every 2–5 minutes
- Evidence storage policy for production (S3/Supabase Storage) and URL signing
- Lock down admin endpoints + rate limits
- Add basic observability (structured logs + alerting)

## Key risk if skipped
If the **no-loophole rule** is not enforced server-side, escrow can be bypassed by direct API calls.
