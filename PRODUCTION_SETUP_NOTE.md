# FlipTrybe Production Setup Note

## Required Environment Variables
- SECRET_KEY
- DATABASE_URL (Postgres)
- FLIPTRYBE_ENV=production
- CORS_ORIGINS
- PAYSTACK_SECRET_KEY (if Paystack enabled)
- PAYSTACK_WEBHOOK_STRICT=1 (optional, to enforce signature validation)
- ADMIN_EMAIL (recommended for seed/admin ops)
- ADMIN_PASSWORD (recommended for seed/admin ops)

## Render Start Command
- gunicorn -b 0.0.0.0:$PORT "app:create_app()"

## Migration Command
- flask db upgrade

## Escrow Runner Cron
- Schedule: every 3 minutes
- Endpoint: POST /api/admin/escrow/run
- Auth: Bearer <admin_token>

Example (Render cron task):
- curl -X POST https://YOUR_BACKEND_URL/api/admin/escrow/run -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

## Notes
- Ensure admin authentication is working before enabling cron.
- Escrow runner should be running continuously in production.
