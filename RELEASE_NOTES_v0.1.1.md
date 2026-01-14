# MicroBridge v0.1.1 Release Notes

This release focuses on **robustness, reliability, and user experience improvements**. Version 0.1.1 addresses critical bugs, adds new features for better workflow efficiency, and significantly improves error handling.

## 🔧 Critical Fixes

### Unified Calibration Point Extraction
- **Issue**: CLI and GUI used different methods for extracting calibration points, causing inconsistent behavior
- **Fix**: Both now use the same dual-method fallback system (annotation → pointlist)
- **Impact**: Ensures consistent, reliable calibration point extraction across both interfaces

### Accurate ShapeCount Validation
- **Issue**: ShapeCount could be inaccurate due to invalid shapes being counted
- **Fix**: Implemented two-pass validation - collect valid shapes first, then write accurate count
- **Impact**: Output XML files now have correct ShapeCount values

### Fail-Safe Mode for Missing Calibration Data
- **Issue**: Missing calibration coordinates silently wrote placeholder (0, 0) values
- **Fix**: Conversion now fails by default with clear error message
- **Impact**: Prevents corrupted output files; users can override with `--force` flag if needed

## ✨ New Features

### Pre-Flight Validation (GUI)
The GUI now validates files and permissions before starting conversion:
- Checks if selected files still exist
- Verifies output folder is writable
- Validates files are readable and properly formatted
- **Benefit**: Catches errors early, saves time on failed batch conversions

### Keyboard Shortcuts (GUI)
Faster workflow with intuitive shortcuts:
- **Ctrl+O**: Open files
- **Ctrl+Q**: Quit application
- **Enter**: Start conversion
- **Delete**: Remove selected files
- **Ctrl+A**: Select all files

### Progress Indication
- Real-time progress updates for files with 10+ shapes
- Shows current shape being processed (e.g., "Shape 15/243")
- **Benefit**: Better visibility into conversion progress for large files

### CLI Flags
- `--force`: Allow placeholder coordinates for missing calibration points (use with caution)
- `--debug`: Show detailed error stack traces for troubleshooting

### Comprehensive Unit Test Suite
- 9 unit tests covering critical functionality
- Sample NDPA/CSV test data files included
- Tests for validation, error handling, and coordinate conversion
- **Benefit**: Ensures reliability and prevents regressions

## 🚀 Improvements

### Enhanced Error Handling
- **Specific exceptions**: FileNotFoundError, PermissionError, ExpatError (XML parsing), ValueError
- **Actionable guidance**: Error messages now suggest concrete solutions
- **Examples**:
  - File not found → Check path and verify file exists
  - Permission denied → Check folder permissions or run as administrator
  - Invalid XML → Validate XML structure or re-export from NDP.view2

### Safe Shutdown Handling
- Changed from daemon to non-daemon threads for proper cleanup
- 10-second grace period for active conversions to finish
- **Benefit**: Prevents corrupted output files from forced termination

### Installer Fixes
- **CLI Installer**: Fixed post-install help display (removed `runhidden` flag)
- **GUI Installer**: Fixed broken uninstall confirmation dialog (removed mutex check)

### Comprehensive Documentation
- **BUILD_INSTRUCTIONS.md**: Complete guide for building executables and installers
- **CHANGELOG.md**: Detailed version history
- **tests/README.md**: Test documentation and usage instructions

## 📊 Statistics

- **15+ bug fixes** across CLI and GUI
- **7 new features** for improved workflow
- **9 unit tests** with 100% pass rate
- **3 new documentation files**

## 🔄 Breaking Changes

**Default behavior change**: Files with missing calibration point coordinates now **fail by default** instead of writing placeholder values. Use `--force` flag to restore old behavior (not recommended).

## 📥 Installation

Download the appropriate installer:
- **MicroBridge_Setup_v0.1.1.exe** - GUI application
- **MicroBridge_CLI_Setup_v0.1.1.exe** - Command-line tool

Or run from source (Python 3.x required):
```bash
python The_Source_Code/MicroBridge_GUI.py
python The_Source_Code/MicroBridge_CLI.py
```

## 📖 Documentation

- [README.md](README.md) - Quick start guide
- [CHANGELOG.md](CHANGELOG.md) - Complete version history
- [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) - Build from source

## 🙏 Acknowledgments

Thank you to all users who provided feedback and bug reports that made this release possible!

---

**Full Changelog**: [v0.1.0...v0.1.1](https://github.com/Snowman-scott/MicroBridge/compare/v0.1.0...v0.1.1)
