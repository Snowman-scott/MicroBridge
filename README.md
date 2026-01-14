# MicroBridge v0.1.1

MicroBridge is a specialized conversion tool designed to bridge Hamamatsu's NDP.view2 digital slide annotation system with Leica Microdissection (LMD) microscope systems. It converts annotation data from `.ndpa` files (and CSV exports) into LMD-compatible XML format.

## Purpose

When working with digital pathology workflows, researchers often annotate regions of interest in NDP.view2 software and need to transfer those annotations to LMD systems for laser microdissection. MicroBridge automates this conversion process, handling coordinate system transformation, calibration point extraction, and batch processing.

## Features

- **GUI Application**: User-friendly interface with real-time progress logging and keyboard shortcuts
- **CLI Tool**: Command-line interface for scripting and batch operations
- **Multiple Input Formats**: Supports both NDPA (XML) and CSV annotation files
- **Batch Processing**: Convert entire folders of annotations at once
- **Pre-flight Validation**: Detects file and permission issues before starting conversion
- **Progress Indication**: Real-time status updates for large files with many shapes
- **Robust Error Handling**: Specific error messages with actionable guidance
- **Dual-Method Calibration**: Extracts calibration points from both circle and freehand annotations
- **Accurate Shape Counting**: Two-pass validation ensures declared ShapeCount matches actual shapes

## Installation

### Pre-built Installers (Windows)

Download the latest installer from the [releases page](https://github.com/Snowman-scott/MicroBridge/releases):

- **MicroBridge_Setup_v0.1.1.exe**: GUI application with full graphical interface
- **MicroBridge_CLI_Setup_v0.1.1.exe**: Command-line tool (can be added to PATH)

### Running from Source

Requires Python 3.x with standard library only (no external dependencies).

```bash
# GUI version
python The_Source_Code/MicroBridge_GUI.py

# CLI version
python The_Source_Code/MicroBridge_CLI.py [files...]
```

For building executables and installers, see [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md).

## Usage

### Important: Annotation Requirements

Your annotation files must follow this structure:

| Region # | Purpose |
|----------|---------|
| 1-3 | **Calibration/Reference Points** - Circle or freehand annotations marking reference positions |
| 4+ | **Capture Shapes** - Freehand regions to be microdissected |

You need a **minimum of 3 regions** (calibration points) for conversion to succeed. Any additional regions become capture shapes.

### GUI Application

1. Launch MicroBridge
2. Select input format (Auto-detect, NDPA, or CSV)
3. Click **Select Files** or **Select Folder** to add annotation files
4. Optionally set a custom output folder
5. Click **Start Conversion**
6. Monitor progress in the real-time log panel

Output files are saved with `_LMD.xml` suffix in the same directory as the input (or your specified output folder).

#### Keyboard Shortcuts

- **Ctrl+O**: Select files to convert
- **Ctrl+Q**: Quit application
- **Enter**: Start conversion (when files are loaded)
- **Delete**: Remove selected files from list
- **Ctrl+A**: Select all files in list

### CLI Application

```bash
# Convert specific files
MicroBridge_CLI.exe annotation1.ndpa annotation2.ndpa

# Convert all .ndpa files in current directory
MicroBridge_CLI.exe

# Allow placeholder coordinates for missing calibration points (not recommended)
MicroBridge_CLI.exe --force annotation.ndpa

# Show detailed error stack traces for debugging
MicroBridge_CLI.exe --debug annotation.ndpa
```

**Note**: By default, files with missing calibration point coordinates will fail conversion. Use `--force` to write placeholder (0, 0) coordinates instead, though this is not recommended for production use.

## File Formats

### Input: NDPA (NDP.view2 Annotation XML)

Native annotation format from Hamamatsu NDP.view2 software containing region annotations with coordinates stored in nanometers. Both circle annotations and freehand/polygon annotations are supported as calibration points.

### Input: CSV

Exported annotation data with coordinates in micrometers. **Note**: CSV exports only contain centroid coordinates, not polygon vertices. Use NDPA format for full shape data.

### Output: LMD-Compatible XML

Produces XML files with 3 calibration points and N capture shapes, formatted for Leica LMD microscope systems. Coordinates are converted from nanometers to micrometers and rounded to integers.

## What's New in v0.1.1

This release focuses on robustness, reliability, and user experience improvements:

### Critical Fixes
- **Unified calibration point extraction**: Both CLI and GUI now use the same dual-method fallback system (annotation → pointlist)
- **Accurate ShapeCount**: Two-pass validation ensures the declared count matches actual shapes
- **Fail-safe mode**: Missing calibration points now fail by default instead of writing silent placeholders

### New Features
- **Pre-flight validation** in GUI catches file/permission errors before conversion starts
- **Keyboard shortcuts** for faster workflow (Ctrl+O, Ctrl+Q, Delete, Ctrl+A, Enter)
- **Progress indication** for large files with real-time shape-by-shape updates
- **CLI flags**: `--force` for placeholder coordinates, `--debug` for detailed error traces
- **Unit test suite** with 9 comprehensive tests and sample data files

### Improvements
- Specific error messages with actionable guidance (file not found, permissions, invalid XML)
- Safe shutdown handling with 10-second grace period for active conversions
- Fixed installer scripts (CLI help visibility, GUI uninstall dialog)
- Comprehensive documentation (BUILD_INSTRUCTIONS.md, CHANGELOG.md, test coverage)

See [CHANGELOG.md](CHANGELOG.md) for complete details.

## Troubleshooting

### "Need at least 3 regions for calibration points"
Your annotation file doesn't have enough regions. Ensure you have at least 3 annotations (circle or freehand) as reference points before your capture shapes.

### "Calibration point missing coordinates"
One or more of the first 3 regions lacks valid coordinate data. MicroBridge now fails by default to prevent silent errors. To proceed with placeholder (0, 0) coordinates, use the `--force` flag in CLI mode.

**Solution**: Check that your reference points in NDP.view2 have valid coordinate data. Both circle annotations and freehand/polygon annotations are supported as calibration points.

### Pre-flight validation errors (GUI)
The GUI checks for common issues before starting conversion:
- **Missing files**: Files that existed when selected but were deleted/moved
- **Permission errors**: Output folder is not writable
- **Invalid files**: Files that cannot be read or are not valid XML/CSV

Fix the reported issues and try again.

### CSV conversion shows "centroids only" warning
CSV exports from NDP.view2 only contain center coordinates, not full polygon vertices. For accurate shape transfer, use the native NDPA format.

### Application won't close during conversion
The GUI uses non-daemon threads for safe shutdown. Click the X button and wait up to 10 seconds for the conversion to finish gracefully. Forcing termination may corrupt output files.

## Testing

MicroBridge includes a comprehensive unit test suite. To run tests:

```bash
cd tests
python -m unittest test_conversion.py
```

Test coverage includes validation of coordinate conversion, calibration extraction, error handling, and ShapeCount accuracy. See [tests/README.md](tests/README.md) for more information.

## Building from Source

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for complete instructions on:
- Creating executables with PyInstaller
- Building Windows installers with Inno Setup
- Automated build scripts

## Dependencies

**Runtime**: Python 3.x standard library only
- `tkinter` - GUI framework
- `xml.dom.minidom` - XML parsing
- `csv` - CSV parsing
- `queue`, `threading` - Thread-safe GUI updates

**Build Tools** (optional):
- PyInstaller - Executable bundling
- Inno Setup - Windows installer creation

## Development Story

This project started from a real need in digital pathology workflow. I wrote a simple proof-of-concept script to convert NDP.view2 annotations to LMD format, and it worked well enough for basic use. From there, I expanded the functionality, added the GUI for easier batch processing, and used AI assistance to polish the code, implement new features, and fix things I didn't know how to do myself.

It's been a practical learning experience - combining domain knowledge from my work with modern AI tools to build something genuinely useful.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

Rose Scott ([@Snowman-scott](https://github.com/Snowman-scott))
