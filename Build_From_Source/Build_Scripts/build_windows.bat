@echo off
SETLOCAL EnableDelayedExpansion

echo ============================================================
echo  MicroBridge: Unified Test & Build (v1.2.0)
echo ============================================================
echo.

REM --- Step 1: Automated Testing ---
echo [1/4] Running Unit Tests with Real Test Data...
REM Set PYTHONPATH so tests can find MicroBridge.py in The_Source_Code folder
set PYTHONPATH=%PYTHONPATH%;%CD%\The_Source_Code
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
echo (Supports both GUI and --cli modes)
echo.

pyinstaller ^
    --name="MicroBridge" ^
    --onedir ^
    --windowed ^
    --icon="The_Source_Code\MicroBridge_Icon.ico" ^
    --version-file="The_Source_Code\version_info.txt" ^
    --add-data="The_Source_Code\MicroBridge_Icon.ico;." ^
    --distpath="dist" ^
    --workpath="build" ^
    --noconfirm ^
    "The_Source_Code\MicroBridge.py"

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
echo   - Double-click: Launches GUI
echo   - Terminal: MicroBridge.exe --cli file.ndpa
echo ============================================================
pause
