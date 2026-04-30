@echo off
setlocal
title Sherlock Mobile App Setup

echo ============================================================
echo  Sherlock Mobile App – Flutter Setup (Windows)
echo ============================================================
echo.

REM Check Flutter
flutter --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Flutter not found.
    echo Install Flutter from https://flutter.dev/docs/get-started/install
    pause & exit /b 1
)

echo [1/4] Creating Flutter project scaffold...
flutter create . --project-name sherlock --org com.sherlock --platforms android,ios
if errorlevel 1 (
    echo ERROR: flutter create failed.
    pause & exit /b 1
)

echo.
echo [2/4] Copying platform config files...
copy /Y android\app\src\main\AndroidManifest.xml android\app\src\main\AndroidManifest.xml.bak >nul 2>&1
REM AndroidManifest.xml already in place from repo

echo.
echo [3/4] Getting Flutter packages...
flutter pub get
if errorlevel 1 (
    echo ERROR: flutter pub get failed.
    pause & exit /b 1
)

echo.
echo [4/4] Done!
echo.
echo  Build Android APK:  flutter build apk --release
echo  Build iOS:          flutter build ios --release  (requires macOS + Xcode)
echo  Run on device:      flutter run
echo.
echo ============================================================
pause
endlocal
