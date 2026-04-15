# MicroBridge Build Instructions (v1.2.0)

Complete guide for building the unified MicroBridge executable from source. MicroBridge 1.2.0 has been consolidated into a single codebase that supports both GUI and CLI operations from a single executable.

## Prerequisites

### Required Software

1. **Python 3.9 - 3.14**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify installation: `python --version`

2. **PyInstaller**
   - Required to package the Python script into a standalone Windows executable.
   ```bash
   pip install pyinstaller
   ```

### Project Structure

Ensure your project follows the unified v1.2.0 structure:
```
MicroBridge/
├── The_Source_Code/
│   ├── MicroBridge.py          <-- Unified GUI/CLI Source
│   ├── MicroBridge_Icon.ico    <-- App Icon
│   └── version_info.txt        <-- Windows Metadata
├── tests/
│   ├── test_data/              <-- Real NDPA/XML samples
│   └── test_*.py               <-- Automated test suite
├── Build_From_Source/
│   └── Build_Scripts/
│       └── build_windows.bat   <-- Recommended Build Script
└── README.md
```

---

## Building Executables

### Option 1: Using Automated Build Script (Recommended)

The automated script ensures code quality by running the full test suite before attempting a build. This prevents shipping an executable with broken conversion logic.

**IMPORTANT:** This script must be run from the **project root directory**.

```batch
# Navigate to project root
cd MicroBridge

# Run the unified build script
Build_From_Source\Build_Scripts\build_windows.bat
```

**This script performs the following steps:**
1. **Validation**: Runs `unittest` against the samples in `tests/test_data/`.
2. **Cleanup**: Wipes previous `build/` and `dist/` directories.
3. **Compilation**: Invokes PyInstaller to create a unified, windowed executable.

**Output Location:**
- `dist/MicroBridge/MicroBridge.exe`

### Option 2: Manual Build (Command Line)

If you wish to skip testing or customize the build process manually, you can run PyInstaller directly from the command line.

**IMPORTANT:** Run these commands from the **project root directory**.

**Windows Command Prompt (CMD):**
```batch
pyinstaller ^
    --name="MicroBridge" ^
    --onedir ^
    --windowed ^
    --icon="The_Source_Code\MicroBridge_Icon.ico" ^
    --version-file="The_Source_Code\version_info.txt" ^
    --add-data="The_Source_Code\MicroBridge_Icon.ico;." ^
    --noconfirm ^
    The_Source_Code\MicroBridge.py
```

**PowerShell / Git Bash / Linux / macOS:**
```bash
pyinstaller \
    --name="MicroBridge" \
    --onedir \
    --windowed \
    --icon="The_Source_Code/MicroBridge_Icon.ico" \
    --version-file="The_Source_Code/version_info.txt" \
    --add-data="The_Source_Code/MicroBridge_Icon.ico;." \
    --noconfirm \
    The_Source_Code/MicroBridge.py
```

**Flags Explained:**
- `--name`: Sets the output executable name.
- `--onedir`: Creates a folder containing the EXE and its dependencies (better for distribution).
- `--windowed`: Hides the console window when launching (GUI mode).
- `--icon`: Applies the MicroBridge icon to the executable.
- `--version-file`: Embeds Windows version metadata (version, author, etc.).
- `--add-data`: Bundles the icon file inside the app folder so the GUI can find it.

---

## Operating Modes

The generated `MicroBridge.exe` is a hybrid binary that handles both user interfaces:

### 1. GUI Mode (Default)
Simply double-click the executable. This launches the Tkinter interface for interactive file selection and conversion.

### 2. CLI Mode (Automation)
Run the executable from a terminal/command prompt to use it in automated pipelines:
```bash
MicroBridge.exe --cli <path_to_file.ndpa>
```
*   `--cli`: Required flag to bypass the GUI.
*   `--force`: Optional flag to ignore missing calibration points (uses placeholder 0,0).

---

## Testing & CI/CD

MicroBridge v1.2.0 includes a comprehensive cross-platform testing suite that runs on every commit.

### Local Testing
Before sharing your build, run the tests manually to ensure compatibility with your local environment:
```bash
# Windows
set PYTHONPATH=The_Source_Code
python -m unittest discover -s tests -p "test_*.py" -v

# macOS/Linux
PYTHONPATH=The_Source_Code python3 -m unittest discover -s tests -p "test_*.py" -v
```

### Automated CI/CD
The project is officially validated via GitHub Actions and GitLab CI across:
- **Operating Systems**: Windows, macOS, Ubuntu.
- **Linux Distributions**: Debian, Arch Linux, Fedora.
- **Python Versions**: 3.9 through 3.14.

---

## Troubleshooting

### "Unit tests failed!"
The build script will abort if tests fail. This usually means a change to `MicroBridge.py` has broken the conversion logic. Check the console output for specific failure details.

### "Icon file not found"
Ensure you are running the build command/script from the **project root**. PyInstaller looks for paths relative to the current working directory.

### Antivirus False Positives
Executables created with PyInstaller are occasionally flagged by antivirus software. This is common for unsigned binaries. For production distribution, consider signing the executable with a code-signing certificate.

---

**Last Updated:** 2026-04-15  
**MicroBridge Version:** 1.2.0
