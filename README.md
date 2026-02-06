# FlipTrybe Fullstack (Backend + Flutter)

You have:
- `backend/` (Flask) = the brain 🧠
- `frontend/` (Flutter) = the face 😄

## Segment checklist (all 8 included)
1. Foundation: boots locally + health + route listing (dev)
2. Bearer tokens: JWT login for Flutter + auto auth on requests
3. DB ready: Flask-Migrate wired + seed-admin endpoint
4. Button wiring helpers: `/dev/routes` + consistent `/api/*` paths
5. Paystack: initialize + verify + webhook skeleton
6. Termii OTP: request/verify (demo mode if key missing)
7. Landing: Flutter intro video plays twice then image
8. Render: runtime.txt + Procfile + render.yaml

---

## Run backend locally (Windows)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLIPTRYBE_ENV="dev"
python main.py
```

Test:
- http://127.0.0.1:5000/health
- http://127.0.0.1:5000/dev/routes

## Run Flutter locally (Android Emulator)
```bash
cd frontend
flutter pub get
flutter run
```

By default Flutter calls:
- http://10.0.2.2:5000 (Android emulator)

## Run Flutter on a real Android phone
1) Put phone + computer on same Wi-Fi  
2) Find your PC IP:
```powershell
ipconfig
```
3) Run Flutter with:
```bash
flutter run --dart-define=BASE_URL=http://YOUR_PC_IP:5000
```

## Put your own landing media
Replace these files:
- `frontend/assets/videos/intro.mp4`
- `frontend/assets/images/landing.png` (or change code to .jpg)


## DB init (dev) + seed admin
If you are testing locally and you don't have migrations yet:

1) Start backend with `FLIPTRYBE_ENV=dev`
2) Create tables:
- POST http://127.0.0.1:5000/dev/db/create-all
3) Create admin (optional):
- POST http://127.0.0.1:5000/dev/seed-admin

## How login works (Flutter)
1) POST /api/auth/otp/request  -> in dev you get `demo_otp` back if Termii isn't configured
2) POST /api/auth/otp/verify   -> returns `token`
3) Flutter stores token and sends it as:
   Authorization: Bearer <token>

If a screen shows nothing, check for a **401** (not logged in) or a missing route in:
- /dev/routes  (dev only)
