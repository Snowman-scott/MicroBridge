# MicroBridge

MicroBridge is a specialized conversion tool designed to bridge Hamamatsu's NDP.view2 digital slide annotation system with Leica Microdissection (LMD) microscope systems. It converts annotation data from `.ndpa` files (and CSV exports) into LMD-compatible XML format.

## Purpose

When working with digital pathology workflows, researchers often annotate regions of interest in NDP.view2 software and need to transfer those annotations to LMD systems for laser microdissection. MicroBridge automates this conversion process, handling:

- Coordinate system transformation (nanometers to micrometers)
- Calibration point extraction
- Shape/polygon vertex conversion
- Batch processing of multiple files

## Features

- **GUI Application**: User-friendly interface with real-time progress logging
- **CLI Tool**: Command-line interface for scripting and batch operations
- **Multiple Input Formats**: Supports both NDPA (XML) and CSV annotation files
- **Batch Processing**: Convert entire folders of annotations at once
- **Thread-Safe**: GUI remains responsive during large batch conversions

## Installation

### Pre-built Installers (Windows)

Download the latest installer from the releases page. Two versions are available:

- **MicroBridge GUI**: Full graphical interface
- **MicroBridge CLI**: Command-line tool (can be added to PATH)

### Running from Source

Requires Python 3.x with standard library only (no external dependencies).

```bash
# GUI version
python The_Source_Code/MicroBridge_GUI.py

# CLI version
python The_Source_Code/MicroBridge_CLI.py [files...]
```

## Usage

### Important: Annotation Requirements

Your annotation files must follow this structure:

| Region # | Purpose |
|----------|---------|
| 1-3 | **Calibration/Reference Points** - Circle annotations marking reference positions |
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

### CLI Application

```bash
# Convert specific files
python MicroBridge_CLI.py annotation1.ndpa annotation2.ndpa

# Convert all .ndpa files in current directory
python MicroBridge_CLI.py
```

## File Formats

### Input: NDPA (NDP.view2 Annotation XML)

Native annotation format from Hamamatsu NDP.view2 software. Contains:
- `ndpviewstate` elements representing annotated regions
- Circle annotations for reference points
- Pointlist data for freehand shapes
- Coordinates stored in **nanometers**

### Input: CSV

Exported annotation data with coordinates. Expected format:
- Header row (skipped)
- Columns 6 and 7 (indices 5, 6) contain X and Y coordinates
- Coordinates assumed to be in **micrometers**

**Note**: CSV exports only contain centroid coordinates, not polygon vertices. Use NDPA format for full shape data.

### Output: LMD-Compatible XML

```xml
<?xml version="1.0" encoding="utf-8"?>
<ImageData>
  <GlobalCoordinates>1</GlobalCoordinates>
  <X_CalibrationPoint_1>12345</X_CalibrationPoint_1>
  <Y_CalibrationPoint_1>67890</Y_CalibrationPoint_1>
  <X_CalibrationPoint_2>...</X_CalibrationPoint_2>
  <Y_CalibrationPoint_2>...</Y_CalibrationPoint_2>
  <X_CalibrationPoint_3>...</X_CalibrationPoint_3>
  <Y_CalibrationPoint_3>...</Y_CalibrationPoint_3>
  <ShapeCount>N</ShapeCount>
  <Shape_1>
    <PointCount>M</PointCount>
    <X_1>...</X_1>
    <Y_1>...</Y_1>
    <!-- Additional vertices -->
  </Shape_1>
  <!-- Additional shapes -->
</ImageData>
```

## Coordinate Conversion

MicroBridge performs the following transformation:
- **NDPA input**: Divides coordinates by 1000 (nm → μm) and rounds to integers
- **CSV input**: Assumes coordinates are already in micrometers, rounds to integers

## Building from Source

### Creating Executables (PyInstaller)

```bash
pyinstaller MicroBridge.spec
```

### Creating Windows Installers (Inno Setup)

Use the provided scripts in `Installer_scripts/`:
- `installer_script_GUI.iss` - GUI application installer
- `installer_script_CLI.iss` - CLI tool installer

## Project Structure

```
MicroBridge/
├── The_Source_Code/
│   ├── MicroBridge_CLI.py      # Command-line interface
│   ├── MicroBridge_GUI.py      # GUI application
│   ├── MicroBridge_Icon.ico    # Application icon
│   └── version_info.txt        # PyInstaller version metadata
├── Installer_scripts/
│   ├── installer_script_CLI.iss
│   └── installer_script_GUI.iss
├── MicroBridge.spec            # PyInstaller configuration
├── README.md
└── LICENSE
```

## Dependencies

**Runtime**: Python 3.x standard library only
- `os`, `sys` - File system operations
- `csv` - CSV parsing
- `queue`, `threading` - Thread-safe GUI updates
- `tkinter` - GUI framework
- `xml.dom.minidom` - XML parsing

**Build Tools** (optional):
- PyInstaller - Executable bundling
- Inno Setup - Windows installer creation

## Troubleshooting

### "Need at least 3 regions for calibration points"
Your annotation file doesn't have enough regions. Ensure you have at least 3 circle annotations as reference points before your capture shapes.

### Calibration point coordinates are 0
The first 3 regions may not have valid circle annotations with x/y coordinates. Check that your reference points in NDP.view2 are circle annotations, not other shapes.

### CSV conversion shows "centroids only" warning
CSV exports from NDP.view2 only contain center coordinates, not full polygon vertices. For accurate shape transfer, use the native NDPA format.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

Rose Scott ([@Snowman-scott](https://github.com/Snowman-scott))
