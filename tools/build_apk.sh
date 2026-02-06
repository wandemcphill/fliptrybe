#!/usr/bin/env bash
set -euo pipefail

# FlipTrybe: build Android release APK
#
# Usage:
#   ./tools/build_apk.sh
#   ./tools/build_apk.sh http://192.168.1.50:5000
#   ./tools/build_apk.sh https://your-render-backend.onrender.com

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
BASE_URL="${1:-}"

cd "$FRONTEND_DIR"
flutter clean
flutter pub get

if [[ -n "$BASE_URL" ]]; then
  flutter build apk --release --dart-define=BASE_URL="$BASE_URL"
else
  flutter build apk --release
fi

echo "APK built: $FRONTEND_DIR/build/app/outputs/flutter-apk/app-release.apk"
