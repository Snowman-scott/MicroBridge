# MicroBridge Changelog

All notable changes to this project will be documented in this file.

## [Version 0.1.1] - 2026-01-09

### 🔧 Critical Fixes

#### Unified Calibration Point Extraction Logic
- **Fixed incompatibility between CLI and GUI versions** - Both tools now use identical logic for extracting calibration points
- **Added dual-method fallback system**:
  - Primary: Extracts from `<annotation>` elements (circle annotations)
  - Fallback: Extracts from `<pointlist><point>` elements (freehand annotations)
  - Last resort: Uses placeholder `0,0` coordinates with clear warning
- **Improved logging** - Now indicates extraction method used: `(from circle annotation)`, `(from pointlist)`, or `(placeholder)`

#### ShapeCount Accuracy Fix
- **Fixed ShapeCount mismatch** - CLI and GUI now use two-pass approach to ensure declared `<ShapeCount>` matches actual shapes written
- Prevents shapes with no points from being counted but skipped during writing
- Ensures LMD-compatible XML schema compliance

### 🛡️ Robustness Improvements

#### Error Handling
- **Improved exception handling** - Now uses specific exception types (`ValueError`, `TypeError`, `AttributeError`) instead of generic catch-all
- **Better coordinate validation** - Gracefully handles malformed/non-numeric coordinate data
- **Consistent calibration point indexing** - Always writes all 3 calibration points even when data is missing

#### Thread Safety (GUI)
- **Removed daemon thread** - Conversion worker thread is now non-daemon to prevent partial file writes on GUI close
- **Added clean shutdown handling** - GUI warns users when closing during active conversion
- **Implemented stop event** - Worker thread checks for cancellation requests and finishes current file safely
- **Added shutdown timeout** - Waits up to 10 seconds for worker to finish gracefully before force-closing

### 📝 Documentation & Metadata

#### Version Consistency
- **Aligned version numbers** - Updated `version_info.txt` to use consistent version `0.1.0.0` across all fields:
  - `filevers`: (1,0,0,0) → (0,1,0,0)
  - `prodvers`: (1,0,0,0) → (0,1,0,0)
  - `FileVersion`: "0.1.5" → "0.1.0.0"
  - `ProductVersion`: "0.1" → "0.1.0.0"
- **Fixed malformed StringStruct** - Added proper `CompanyName` key (set to empty string for individual developer)
- **Added LegalCopyright field** - "Copyright (c) 2024 Rose Scott"

#### Installer Improvements
- **Fixed CLI installer post-install action** - Removed `runhidden` flag so help output is visible
- **Updated GUI installer URL** - Changed placeholder to actual GitHub repository: `https://github.com/Snowman-scott/MicroBridge`
- **Improved uninstall dialog** - Removed broken mutex check, replaced with clear user warning
- **Removed unused variable** - Deleted unused `ErrorCode` variable from uninstall function

### 🧪 Testing & Quality Assurance

#### Unit Test Suite
- **Created comprehensive test suite** with 9 tests covering:
  - Valid NDPA conversion with multiple shapes
  - Insufficient calibration points handling
  - Missing calibration coordinates (with/without `--force`)
  - Non-existent file error handling
  - Invalid XML format handling
  - Coordinate conversion accuracy (nm → μm)
  - ShapeCount accuracy verification
  - Output file naming conventions
- **Sample test data** included in `tests/test_data/`:
  - `valid_sample.ndpa` - Valid NDPA with 3 calibration + 2 shapes
  - `valid_sample.csv` - Valid CSV for future testing
- **Tests use only Python standard library** - No additional dependencies
- **Run tests:** `python -m unittest tests/test_conversion.py`

### 🔍 Code Quality & User Experience

#### Keyboard Shortcuts (GUI)
- **Ctrl+O** - Open files
- **Ctrl+Shift+O** - Open folder
- **Ctrl+Q** - Quit application
- **Enter** - Start conversion (when files selected)
- **Delete/Backspace** - Remove selected files from list
- **Ctrl+A** - Select all files in list
- **Improves productivity** for power users

#### Progress Indication for Large Files (GUI)
- **Shows individual shape progress** for files with >10 shapes
- **Updates progress text** during conversion: "Converting: file.ndpa (Shape 47/120)"
- **Prevents UI appearing frozen** during long conversions
- **Real-time feedback** keeps users informed

#### Build Instructions
- **Created BUILD_INSTRUCTIONS.md** with complete build guide:
  - PyInstaller setup and usage
  - Inno Setup installer compilation
  - Automated build script example
  - Troubleshooting common issues
  - Clean build procedures
  - Distribution checklist
- **Makes project easier to build and distribute**

#### Placeholder Calibration Points - Now an Error by Default
- **CLI**: Conversion now **fails** when calibration points are missing (prevents bad output files)
  - Added `--force` flag to explicitly allow placeholder (0,0) coordinates
  - Shows clear error message with actionable fix instructions
- **GUI**: Conversion now **stops** when calibration points are missing
  - Displays detailed error in log with steps to fix in NDP.view2
  - No more silent failures that could break LMD system

#### Pre-Flight Validation (GUI)
- **Added comprehensive validation before conversion starts**:
  - Verifies all files still exist (warns if deleted after adding to list)
  - Checks output folder write permissions
  - Validates files are readable
  - Quick format check (.ndpa should be XML, .csv shouldn't be XML)
- **Shows detailed error dialog** listing all issues found
- **Prevents wasted time** on conversions that will fail

#### Improved Error Messages
- **Specific error handling** for common issues in both CLI and GUI:
  - `FileNotFoundError` → "File may have been moved or deleted"
  - `PermissionError` → "Choose different output folder with write permissions"
  - `XML parsing errors` → "File may be corrupted, try opening in NDP.view2"
  - `ValueError` → "Invalid coordinate data, check annotations in NDP.view2"
  - `Unexpected errors` → Links to GitHub issues page with debug info
- **CLI**: Added `--debug` flag to show full stack traces only when needed
- **GUI**: Always includes debug information in log for troubleshooting

### ⚠️ Breaking Changes

**Minor behavior change**: Missing calibration points now cause conversion to **fail by default** (previously wrote placeholder `0,0` coordinates silently).

**Migration**: If you have NDPA files with missing calibration data:
- **Recommended**: Fix the annotations in NDP.view2 (add valid calibration points)
- **Workaround**: Use `--force` flag in CLI to allow placeholder coordinates (not recommended)

### 📌 Known Limitations
- CSV exports only contain centroid coordinates, not full polygon vertices
- Installer scripts are Windows-only (source code works cross-platform)
- No automated tests yet (planned for v0.2.0)

---

## [Version 0.1.0] - Initial Release

### Features
- GUI application for batch conversion
- CLI tool for scripting and automation
- NDPA to LMD XML conversion
- CSV to LMD XML conversion
- Coordinate transformation (nanometers → micrometers)
- Three calibration points + N capture shapes output format
- Thread-safe GUI with real-time progress logging
- Batch processing support

### Requirements
- Python 3.x (standard library only)
- Windows (installer scripts)

---

## Upgrade Notes

### From 0.1.0 to 0.1.1

**No action required** - Simply install the new version. All existing workflows will continue to function.

**Improved compatibility**: If you previously experienced different results between CLI and GUI for the same NDPA file, this has been resolved in v0.1.1.


