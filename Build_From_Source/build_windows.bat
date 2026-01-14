@echo off
REM MicroBridge Windows Build Script
REM Run this from the project root directory on Windows

echo ============================================================
echo  MicroBridge Build Script for Windows
echo ============================================================
echo.

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed.
    echo Install it with: pip install pyinstaller
    pause
    exit /b 1
)

echo [1/2] Building GUI version...
echo.

pyinstaller ^
    --name="MicroBridge" ^
    --onedir ^
    --windowed ^
    --icon="The_Source_Code\MicroBridge_Icon.ico" ^
    --add-data="The_Source_Code\MicroBridge_Icon.ico;." ^
    --version-file="The_Source_Code\version_info.txt" ^
    --distpath="dist" ^
    --workpath="build" ^
    --noconfirm ^
    "The_Source_Code\MicroBridge_GUI.py"

if errorlevel 1 (
    echo.
    echo ERROR: GUI build failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Building CLI version...
echo.

pyinstaller ^
    --name="MicroBridge_CLI" ^
    --onefile ^
    --console ^
    --icon="The_Source_Code\MicroBridge_Icon.ico" ^
    --version-file="The_Source_Code\version_info.txt" ^
    --distpath="dist" ^
    --workpath="build" ^
    --noconfirm ^
    "The_Source_Code\MicroBridge_CLI.py"

if errorlevel 1 (
    echo.
    echo ERROR: CLI build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Build Complete!
echo ============================================================
echo.
echo Output:
echo   GUI: dist\MicroBridge\MicroBridge.exe
echo   CLI: dist\MicroBridge_CLI.exe
echo.
echo The icon file is included in the GUI dist folder.
echo.
pause
