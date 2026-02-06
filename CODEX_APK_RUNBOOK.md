# FlipTrybe APK Runbook (for Codex)

## Repo layout
- `frontend/` Flutter (produces the APK)
- `backend/`  Flask API

## API base URL wiring
Flutter reads the API base URL from:
- `--dart-define=BASE_URL=http://YOUR_BASE_URL`
- default: `http://10.0.2.2:5000` (Android emulator -> your PC)

## 1) Backend (local)

### macOS/Linux
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLIPTRYBE_ENV=dev
python main.py
```

### Windows (PowerShell)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLIPTRYBE_ENV="dev"
python main.py
```

Smoke tests:
- http://127.0.0.1:5000/health
- http://127.0.0.1:5000/dev/routes

## 2) Flutter (debug run)

### Android Emulator
```bash
cd frontend
flutter pub get
flutter run
```

### Real Android phone (same Wi‑Fi as your PC)
```bash
cd frontend
flutter pub get
flutter run --dart-define=BASE_URL=http://YOUR_PC_IP:5000
```

## 3) Build an APK (release)
```bash
cd frontend
flutter clean
flutter pub get
flutter build apk --release
```

Output:
- `frontend/build/app/outputs/flutter-apk/app-release.apk`

## Notes
- If you deploy the backend on Render, set `BASE_URL` to the Render service URL.
- If you see a blank screen, check backend logs and Flutter logs for 401 (missing token) or 404 (route not registered).
