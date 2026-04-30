@echo off
setlocal
title Sherlock – Build Windows Installer

echo ============================================================
echo  Sherlock – Windows Installer Builder
echo ============================================================
echo.

REM ── Step 1: Check Python ────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Install Python 3.9+ from https://python.org
    pause & exit /b 1
)

REM ── Step 2: Install Python dependencies ────────────────────────────────────
echo [1/3] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause & exit /b 1
)

REM ── Step 3: Build Sherlock.exe with PyInstaller ─────────────────────────────
echo [2/3] Building Sherlock.exe...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "Sherlock" ^
    --add-data "..\sherlock_project\resources\data.json;sherlock_project\resources" ^
    --add-data "..\sherlock_project\resources\data.schema.json;sherlock_project\resources" ^
    --hidden-import=sherlock_project ^
    --hidden-import=sherlock_project.sherlock ^
    --hidden-import=sherlock_project.sites ^
    --hidden-import=sherlock_project.result ^
    --hidden-import=sherlock_project.notify ^
    --hidden-import=requests_futures.sessions ^
    --hidden-import=colorama ^
    --hidden-import=pandas ^
    --hidden-import=tomli ^
    --paths ".." ^
    --distpath "dist" ^
    --workpath "build_tmp" ^
    --specpath "." ^
    sherlock_gui.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause & exit /b 1
)

REM ── Step 4: Build installer with Inno Setup ─────────────────────────────────
echo [3/3] Building SherlockSetup.exe installer...

REM Look for Inno Setup in common install locations
set ISCC=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else (
    echo.
    echo  WARNING: Inno Setup 6 not found.
    echo  Download from: https://jrsoftware.org/isinfo.php
    echo.
    echo  Sherlock.exe is already built in dist\Sherlock.exe
    echo  You can distribute that file directly without an installer,
    echo  or install Inno Setup and re-run this script.
    echo.
    goto :done
)

mkdir installer_output 2>nul
"%ISCC%" installer.iss
if errorlevel 1 (
    echo ERROR: Inno Setup compilation failed.
    pause & exit /b 1
)

echo.
:done
echo ============================================================
echo  Build complete!
echo.
if exist "dist\Sherlock.exe"           echo   Standalone exe : dist\Sherlock.exe
if exist "installer_output\SherlockSetup.exe" echo   Installer      : installer_output\SherlockSetup.exe
echo.
echo  SherlockSetup.exe installs Sherlock to Program Files,
echo  adds a Start Menu entry, and registers an uninstaller.
echo ============================================================
pause
endlocal
