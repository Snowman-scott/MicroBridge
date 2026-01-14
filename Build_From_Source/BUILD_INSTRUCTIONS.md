# MicroBridge Build Instructions

Complete guide for building MicroBridge executables and installers from source.

## Prerequisites

### Required Software

1. **Python 3.7+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify installation: `python --version`

2. **PyInstaller**
   ```bash
   pip install pyinstaller
   ```

3. **Inno Setup 6+** (Windows only - for creating installers)
   - Download from [jrsoftware.org](https://jrsoftware.org/isdl.php)
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

### Project Structure

Ensure your project has this structure:
```
MicroBridge/
├── The_Source_Code/
│   ├── MicroBridge_CLI.py
│   ├── MicroBridge_GUI.py
│   ├── MicroBridge_Icon.ico
│   └── version_info.txt
├── Installer_scripts/
│   ├── installer_script_CLI.iss
│   └── installer_script_GUI.iss
├── MicroBridge.spec
└── README.md
```

---

## Building Executables

### Option 1: Using Automated Build Script (Easiest)

**IMPORTANT:** The build scripts **MUST** be run from the project root directory, not from inside the `Build_From_Source` folder.

```bash
# Navigate to project root
cd /path/to/MicroBridge

# Run the Windows build script
Build_From_Source\build_windows.bat
```

This script will:
1. Build the GUI version (`MicroBridge.exe`)
2. Build the CLI version (`MicroBridge_CLI.exe`)
3. Place outputs in the `dist/` folder

**Output locations:**
- GUI: `dist/MicroBridge/MicroBridge.exe` (with `_internal/` folder)
- CLI: `dist/MicroBridge_CLI/MicroBridge_CLI.exe` (with `_internal/` folder)

### Option 2: Using PyInstaller Spec File

The included `MicroBridge.spec` file configures the GUI build with all necessary settings.

```bash
# Navigate to project root
cd /path/to/MicroBridge

# Build GUI using spec file
pyinstaller MicroBridge.spec
```

**Output:** `dist/MicroBridge/` folder containing:
- `MicroBridge.exe`
- `_internal/` folder with dependencies

### Option 3: Building GUI Manually

If you need to customize the build or the spec file is missing:

**IMPORTANT:** Run from the project root directory.

**Recommended:** Use the automated build script (Option 1) or spec file (Option 2) instead of manual commands.

**Windows Command Prompt:**
```batch
pyinstaller --name="MicroBridge" --onedir --windowed --icon="The_Source_Code\MicroBridge_Icon.ico" --version-file="The_Source_Code\version_info.txt" --add-data="The_Source_Code\MicroBridge_Icon.ico;." The_Source_Code\MicroBridge_GUI.py
```

**PowerShell / Unix / Git Bash:**
```bash
pyinstaller --name="MicroBridge" --onedir --windowed --icon="The_Source_Code/MicroBridge_Icon.ico" --version-file="The_Source_Code/version_info.txt" --add-data="The_Source_Code/MicroBridge_Icon.ico;." The_Source_Code/MicroBridge_GUI.py
```

**Flags explained:**
- `--onedir`: Creates a folder with executable and dependencies (required by installer script)
- `--windowed`: No console window (GUI only)
- `--icon`: Application icon
- `--version-file`: Windows version metadata
- `--add-data`: Include icon in bundle

### Building CLI

For the command-line version:

**Recommended:** Use the automated build script (Option 1) instead of manual commands.

**Windows Command Prompt:**
```batch
pyinstaller --name="MicroBridge_CLI" --onedir --console --icon="The_Source_Code\MicroBridge_Icon.ico" --version-file="The_Source_Code\version_info.txt" The_Source_Code\MicroBridge_CLI.py
```

**PowerShell / Unix / Git Bash:**
```bash
pyinstaller --name="MicroBridge_CLI" --onedir --console --icon="The_Source_Code/MicroBridge_Icon.ico" --version-file="The_Source_Code/version_info.txt" The_Source_Code/MicroBridge_CLI.py
```

**Flags explained:**
- `--onedir`: Creates a folder with executable and dependencies (consistent with GUI)
- `--console`: Shows console window for CLI output

**Output:** `dist/MicroBridge_CLI/MicroBridge_CLI.exe`

---

## Building Installers

After building the executables, create Windows installers using Inno Setup.

### Prepare Build Outputs

Ensure your directory structure matches the installer script expectations:

**For GUI Installer:**
```
MicroBridge/
├── MicroBridge_/
│   └── MicroBridge/
│       ├── MicroBridge.exe
│       └── _internal/
│           └── (all dependencies)
└── Installer_scripts/
    └── installer_script_GUI.iss
```

**Note:** The installer expects `MicroBridge_\MicroBridge\` path. If PyInstaller created just `dist/MicroBridge/`, rename `dist/` to `MicroBridge_/`.

**For CLI Installer:**
```
MicroBridge/
├── dist/
│   └── MicroBridge_CLI/
│       ├── MicroBridge_CLI.exe
│       └── _internal/
│           └── (all dependencies)
└── Installer_scripts/
    └── installer_script_CLI.iss
```

### Compile Installers

#### Method 1: Using Inno Setup GUI

1. Open Inno Setup Compiler
2. File → Open → Select `Installer_scripts/installer_script_GUI.iss` (or `_CLI.iss`)
3. Build → Compile
4. Installer will be created in `Installer_scripts/installer_output/`

#### Method 2: Command Line

```bash
# GUI Installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" Installer_scripts\installer_script_GUI.iss

# CLI Installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" Installer_scripts\installer_script_CLI.iss
```

### Installer Outputs

- **GUI**: `MicroBridge_Setup_v0.1.1.exe`
- **CLI**: `MicroBridge_CLI_Setup_v0.1.1.exe`

Both installers will be in: `Installer_scripts/installer_output/`

---

## Complete Build Process

### Full Automated Build (Recommended)

Create a build script to automate the entire process:

**build_all.bat** (Windows):
```batch
@echo off
echo ========================================
echo Building MicroBridge v0.1.1
echo ========================================

echo.
echo [1/4] Building GUI executable...
pyinstaller MicroBridge.spec
if %errorlevel% neq 0 (
    echo ERROR: GUI build failed
    exit /b 1
)

echo.
echo [2/4] Building CLI executable...
pyinstaller --name="MicroBridge_CLI" --onedir --console --icon="The_Source_Code/MicroBridge_Icon.ico" --version-file="The_Source_Code/version_info.txt" The_Source_Code/MicroBridge_CLI.py
if %errorlevel% neq 0 (
    echo ERROR: CLI build failed
    exit /b 1
)

echo.
echo [3/4] Preparing installer directories...
if not exist "MicroBridge_" mkdir MicroBridge_
if exist "dist\MicroBridge" (
    xcopy /E /I /Y "dist\MicroBridge" "MicroBridge_\MicroBridge\"
)

echo.
echo [4/4] Building installers...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" Installer_scripts\installer_script_GUI.iss
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" Installer_scripts\installer_script_CLI.iss

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo Installers created in: Installer_scripts\installer_output\
echo   - MicroBridge_Setup_v0.1.1.exe (GUI)
echo   - MicroBridge_CLI_Setup_v0.1.1.exe (CLI)
echo.
pause
```

**Usage:**
```bash
# Run from project root
build_all.bat
```

---

## Testing Builds

### Test Executables Before Creating Installers

**GUI:**
```bash
# Run the built executable
dist\MicroBridge\MicroBridge.exe
```

**CLI:**
```bash
# Test with help flag
dist\MicroBridge_CLI.exe --help

# Test conversion
dist\MicroBridge_CLI.exe test_file.ndpa
```

### Test Installers

1. Run the installer on a clean test machine (or VM)
2. Verify installation completes without errors
3. Test installed application functionality
4. Verify uninstall removes all files

---

## Troubleshooting

### Common Issues

#### "PyInstaller is not recognized"
```bash
# Install PyInstaller
pip install pyinstaller

# Or use full path
python -m PyInstaller MicroBridge.spec
```

#### "Icon file not found"
- Verify `MicroBridge_Icon.ico` exists in `The_Source_Code/`
- Check path is relative to project root

#### "Module not found" errors

**Clean PyInstaller cache:**
```bash
pyinstaller --clean MicroBridge.spec
```

**Manually delete build artifacts:**

Windows Command Prompt:
```batch
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q __pycache__
```

PowerShell:
```powershell
Remove-Item -Recurse -Force build, dist, __pycache__ -ErrorAction SilentlyContinue
```

#### Installer fails: "Source file not found"
- Check that `MicroBridge_\MicroBridge\MicroBridge.exe` exists
- For CLI: Check `dist\MicroBridge_CLI\MicroBridge_CLI.exe` exists
- Paths in `.iss` files are relative to the script location

#### Antivirus flags executable
- This is common with PyInstaller builds
- Submit to antivirus vendor as false positive
- Sign the executable with a code signing certificate (optional)

### Build Size Optimization

Default builds can be large. To reduce the executable size, you can exclude unused modules. There are two methods depending on your build process:

**1. Manual Build: Using `--exclude-module` Flag**

When building manually from the command line (without a `.spec` file), use the `--exclude-module` flag for each module you want to exclude.

*Example:*
```bash
pyinstaller --onedir --windowed --exclude-module matplotlib --exclude-module numpy The_Source_Code/MicroBridge_GUI.py
```

**2. Spec File Build: Editing `Analysis.excludes`**

PyInstaller **ignores** the `--exclude-module` command-line flag when you build using a `.spec` file.

To exclude modules, you **must** edit the `MicroBridge.spec` file and add the module names to the `excludes` list inside the `Analysis` section.

*Example `MicroBridge.spec` modification:*
```python
# In MicroBridge.spec
a = Analysis(
    ['The_Source_Code/MicroBridge_GUI.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    # Add modules to exclude here
    excludes=['matplotlib', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)
```

**Note:** MicroBridge only uses Python's standard library. Excluding third-party modules like `numpy` or `matplotlib` may not be necessary unless they are being incorrectly bundled from your local Python environment, and thus may have minimal effect on build size.

---

## Version Updates

When releasing a new version, update these files:

1. **version_info.txt**
   - Update `filevers` and `prodvers` tuples
   - Update `FileVersion` and `ProductVersion` strings

2. **Installer scripts** (`installer_script_GUI.iss` and `installer_script_CLI.iss`)
   - Update `#define MyAppVersion "0.1"` to new version

3. **CHANGELOG.md**
   - Document all changes in new version section

4. **README.md**
   - Update version numbers if mentioned

---

## Clean Build

To ensure a fresh build without cached files:

```bash
# Delete build artifacts
rmdir /S /Q build dist MicroBridge_ __pycache__

# Delete PyInstaller cache
rmdir /S /Q %LOCALAPPDATA%\pyinstaller

# Rebuild
pyinstaller --clean MicroBridge.spec
```

---

## Distribution Checklist

Before releasing installers:

- [ ] Version numbers updated in all files
- [ ] CHANGELOG.md updated
- [ ] Tested on clean Windows installation
- [ ] All features working (conversion, batch, GUI controls)
- [ ] Error handling works correctly
- [ ] Installers create proper shortcuts
- [ ] Uninstaller removes all files
- [ ] No antivirus false positives (or documented)
- [ ] README.md reflects current version

---

## Platform-Specific Notes

### Windows
- Builds work on Windows 7, 10, and 11
- PyInstaller creates Windows-only executables
- Inno Setup requires Windows

### macOS/Linux
- GUI and CLI source code work on all platforms
- No installer scripts provided (use source directly)
- Users can create their own PyInstaller builds:
  ```bash
  pyinstaller --onefile --windowed MicroBridge_GUI.py
  ```

---

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [Python Packaging Guide](https://packaging.python.org/)

---

## Support

If you encounter build issues:

1. Check this guide's Troubleshooting section
2. Verify all prerequisites are installed
3. Try a clean build
4. Report persistent issues at: https://github.com/Snowman-scott/MicroBridge/issues

---

**Last Updated:** 2026-01-09  
**MicroBridge Version:** 0.1.1
