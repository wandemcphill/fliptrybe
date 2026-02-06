# Codex Command Book (Do not improvise)

## Local backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
flask db init || true
flask db migrate -m "codex changes"
flask db upgrade
python main.py
```

## Local Flutter
```bash
cd frontend
flutter doctor
flutter pub get
flutter run
```

## Release builds
```bash
cd frontend
flutter build apk --release
flutter build appbundle --release
```

## Render
Start:
```bash
gunicorn -b 0.0.0.0:$PORT "app:create_app()"
```
Migrate:
```bash
flask db upgrade
```

## Escrow runner
Schedule every 2-5 minutes:
```bash
curl -X POST https://YOUR_BACKEND/api/admin/escrow/run -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```
