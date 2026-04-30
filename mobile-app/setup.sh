#!/usr/bin/env bash
set -e
echo "============================================================"
echo " Sherlock Mobile App – Flutter Setup (macOS / Linux)"
echo "============================================================"
echo

# Check Flutter
if ! command -v flutter &>/dev/null; then
  echo "ERROR: Flutter not found."
  echo "Install from https://flutter.dev/docs/get-started/install"
  exit 1
fi

echo "[1/4] Creating Flutter project scaffold..."
flutter create . --project-name sherlock --org com.sherlock --platforms android,ios

echo
echo "[2/4] Platform config files already present in repo."

echo
echo "[3/4] Getting Flutter packages..."
flutter pub get

echo
echo "[4/4] Done!"
echo
echo "  Build Android APK : flutter build apk --release"
echo "  Build iOS App     : flutter build ios --release   (macOS + Xcode)"
echo "  Run on device     : flutter run"
echo
echo "============================================================"
