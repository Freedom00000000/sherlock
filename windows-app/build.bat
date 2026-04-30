@echo off
setlocal
title Sherlock Windows Builder

echo ============================================================
echo  Sherlock Windows App Builder
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.9+ from python.org
    pause & exit /b 1
)

REM Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause & exit /b 1
)

echo [2/3] Building Sherlock.exe with PyInstaller...
echo.

REM Run PyInstaller from the windows-app directory.
REM --onefile       : single .exe
REM --windowed      : no console window (GUI only)
REM --add-data      : bundle data.json and schema into the exe
REM --hidden-import : ensure sherlock_project sub-modules are included

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
    echo.
    echo ERROR: PyInstaller build failed. See output above.
    pause & exit /b 1
)

echo.
echo [3/3] Done!
echo.
echo  Sherlock.exe is in:  %~dp0dist\Sherlock.exe
echo.
echo  You can move Sherlock.exe anywhere — it is fully self-contained.
echo ============================================================
pause
endlocal
