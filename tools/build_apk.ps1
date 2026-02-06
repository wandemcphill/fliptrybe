Param(
  [string]$BaseUrl = ""
)

# FlipTrybe: build Android release APK
# Usage:
#   .\tools\build_apk.ps1
#   .\tools\build_apk.ps1 -BaseUrl http://192.168.1.50:5000
#   .\tools\build_apk.ps1 -BaseUrl https://your-render-backend.onrender.com

Push-Location (Join-Path $PSScriptRoot "..\frontend")
flutter clean
flutter pub get

if ($BaseUrl -ne "") {
  flutter build apk --release --dart-define=BASE_URL=$BaseUrl
} else {
  flutter build apk --release
}

Write-Host "APK built: $(Resolve-Path .\build\app\outputs\flutter-apk\app-release.apk)"
Pop-Location
