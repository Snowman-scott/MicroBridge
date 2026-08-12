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
echo [1/5] Running Unit Tests with Real Test Data...
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
echo [2/5] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo Done.

REM --- Step 3: Build GUI (windowed, onedir) ---
echo.
echo [3/5] Building GUI executable (windowed)...
echo.
echo NOTE: onedir builds avoid the Defender false positives that
echo       onefile builds trigger. The .exe lives in a folder.
echo.

pyinstaller ^
    --name="MicroBridge" ^
    --onedir ^
    --windowed ^
    --icon="src\MicroBridge_Icon.ico" ^
    --version-file="Build_From_Source\Build_Scripts\version_info.txt" ^
    --add-data="src\MicroBridge_Icon.ico;." ^
    --distpath="dist" ^
    --workpath="build" ^
    --noconfirm ^
    "src\MicroBridge\main.py"

if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: GUI build failed!
    pause
    exit /b 1
)

REM --- Step 4: Build CLI (console, onedir) ---
echo.
echo [4/5] Building CLI executable (console)...
echo.

pyinstaller ^
    --name="MicroBridge_CLI" ^
    --onedir ^
    --console ^
    --icon="src\MicroBridge_Icon.ico" ^
    --version-file="Build_From_Source\Build_Scripts\version_info.txt" ^
    --distpath="dist" ^
    --workpath="build" ^
    --noconfirm ^
    "src\MicroBridge\main.py"

if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: CLI build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  DONE: Build successful!
echo ============================================================
echo.
echo GUI: dist\MicroBridge\MicroBridge.exe
echo CLI: dist\MicroBridge_CLI\MicroBridge_CLI.exe
echo.
echo Usage:
echo   - Double-click MicroBridge.exe: Launches GUI
echo   - Terminal: MicroBridge_CLI.exe filename.ndpa
echo ============================================================
if not defined CI pause
