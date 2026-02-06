# FlipTrybe Backend (Flask) - Render Ready

Think of this backend as the **brain** 🧠 of your app.

## What’s inside
- Flask API
- Postgres support (Render)
- JWT Bearer tokens for Flutter (mobile-friendly)
- Dev tools (only when `FLIPTRYBE_ENV=dev`)
  - `/dev/routes` shows all endpoints
  - `/dev/env` shows missing env vars
  - `/dev/seed-admin` creates an admin user

---

## Run locally (Windows, like you're 10 😄)

1. Open this `backend/` folder in VS Code.
2. Open Terminal in VS Code.
3. Make a “toy box” (virtual env):

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   If you see `(venv)` then it’s ON ✅

4. Install the lego pieces:

   ```powershell
   pip install -r requirements.txt
   ```

5. Set dev mode (so dev tools work):

   ```powershell
   $env:FLIPTRYBE_ENV="dev"
   ```

6. Start the brain:

   ```powershell
   python main.py
   ```

7. Check it’s alive:

   - http://127.0.0.1:5000/health
   - http://127.0.0.1:5000/dev/routes

---

## Run from a real Android phone
- Phone must be on the **same Wi-Fi** as your computer.
- Find your computer IP:

  ```powershell
  ipconfig
  ```

  Look for `IPv4 Address` like `192.168.1.50`

- Your Flutter base URL should be:
  `http://192.168.1.50:5000`

---

## Deploy to Render
1. Push `backend/` to GitHub.
2. Create a Render Web Service (Python).
3. Render will use `runtime.txt`, `Procfile`, or `render.yaml`.
4. Set environment variables in Render:
   - `FLIPTRYBE_ENV=prod`
   - `SECRET_KEY=...`
   - `DATABASE_URL=...`
   - (optional) `PAYSTACK_SECRET_KEY`, `TERMII_API_KEY`, etc.

Start command:
```bash
gunicorn wsgi:app --bind 0.0.0.0:$PORT
```
