:<<"::CMDLITERAL"
@echo off
goto :WINDOWS_MODE
::CMDLITERAL
echo [Mac/Linux Detected] Forwarding build script to Wine...
wine cmd /c "%~nx0" 2>nul || wine cmd /c "$0"
exit

:WINDOWS_MODE
@echo off
SETLOCAL EnableDelayedExpansion
echo ============================================================
echo  MicroBridge: Unified Test ^& Build
echo ============================================================
echo.

REM --- Step 1: Automated Testing ---
echo [1/4] Running Unit Tests with Real Test Data...
REM Set PYTHONPATH so tests can find MicroBridge in the src folder
set PYTHONPATH=%PYTHONPATH%;%CD%\src
python -m unittest discover -s tests -p "test_*.py" -v

if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: Unit tests failed!
    echo Please fix the code before building.
    pause
    exit /b 1
)
echo SUCCESS: All tests passed.

REM --- Step 2: Cleanup ---
echo.
echo [2/4] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo Done.

REM --- Step 3: Single Unified Build ---
echo.
echo [3/4] Building Unified MicroBridge Executable...
echo (Supports both GUI and CLI modes)
echo.
echo NOTE: onedir avoids the Defender false positives that
echo       onefile builds trigger. The .exe lives in a folder.
echo.

pyinstaller ^
    --name="MicroBridge" ^
    --onedir ^
    --console ^
    --icon="src\MicroBridge_Icon.ico" ^
    --version-file="Build_From_Source\Build_Scripts\version_info.txt" ^
    --add-data="src\MicroBridge_Icon.ico;." ^
    --distpath="dist" ^
    --workpath="build" ^
    --noconfirm ^
    "src\MicroBridge\main.py"

if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  DONE: Build successful!
echo ============================================================
echo Location: dist\MicroBridge\MicroBridge.exe
echo.
echo Usage:
echo   - Double-click: Launches GUI automatically (console hides itself)
echo   - Terminal: MicroBridge.exe filename.ndpa
echo ============================================================
if not defined CI pause
