# MicroBridge

**Convert NDP.view2 annotations to Leica LMD format**

MicroBridge bridges Hamamatsu's NDP.view2 digital slide annotation system with Leica Microdissection (LMD) microscopes. It converts `.ndpa` annotation files into LMD-compatible XML format, handling coordinate transformation and calibration point extraction automatically.

---

## Download

**[Latest Release: v0.1.1](https://github.com/Snowman-scott/MicroBridge/releases/latest)**

| Download | Description |
|----------|-------------|
| `MicroBridge_GUI_v0.1.1.zip` | Graphical interface for interactive use |
| `MicroBridge_CLI_v0.1.1.zip` | Command-line tool for scripting |

Both versions produce identical output. Choose based on your workflow.

---

## Features

- **Dual Interface** - GUI for interactive use, CLI for automation
- **Batch Processing** - Convert entire folders at once
- **Multiple Formats** - Supports NDPA and CSV input files
- **Pre-flight Validation** - Catches errors before conversion starts
- **Real-time Progress** - Live updates for large file processing
- **Robust Error Handling** - Clear messages with actionable solutions

---

## Quick Start

### GUI

1. Download and extract `MicroBridge_GUI_v0.1.1.zip`
2. Run the installer
3. Launch MicroBridge
4. Select files → Start Conversion

### CLI

```bash
# Convert all NDPA files in current directory
MicroBridge_CLI.exe

# Convert specific files
MicroBridge_CLI.exe annotation1.ndpa annotation2.ndpa

# Show help
MicroBridge_CLI.exe --help
```

---

## Annotation Structure

Your annotation files must follow this format:

| Region | Purpose |
|--------|---------|
| 1-3 | **Calibration Points** - Reference markers (circle or freehand) |
| 4+ | **Capture Shapes** - Regions for microdissection |

Minimum 3 regions required. Calibration points can be either circle annotations or freehand/polygon annotations.

---

## File Formats

| Input | Output |
|-------|--------|
| `.ndpa` - NDP.view2 native XML | `_LMD.xml` - Leica LMD format |
| `.csv` - NDP.view2 export | `_LMD.xml` - Leica LMD format |

Coordinates are automatically converted from nanometers to micrometers.

---

## Running from Source

No external dependencies required - uses Python standard library only.

```bash
# GUI
python The_Source_Code/MicroBridge_GUI.py

# CLI
python The_Source_Code/MicroBridge_CLI.py [files...]
```

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for creating executables and installers.

---

## What's New in v0.1.1

- **Unified calibration extraction** - Consistent behavior between CLI and GUI
- **Pre-flight validation** - Catches file/permission issues early
- **Keyboard shortcuts** - Ctrl+O, Ctrl+Q, Enter, Delete, Ctrl+A
- **Progress indication** - Real-time updates for large files
- **Fail-safe mode** - Missing calibration data fails by default
- **Comprehensive tests** - 9 unit tests with sample data

See [CHANGELOG.md](CHANGELOG.md) for complete details.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Need at least 3 regions" | Add more annotations as calibration points |
| "Calibration point missing coordinates" | Verify reference points have valid coordinate data in NDP.view2 |
| CSV shows "centroids only" | Use NDPA format for full polygon vertices |
| Permission errors | Check output folder permissions or run as administrator |

---

## Documentation

- [CHANGELOG.md](CHANGELOG.md) - Version history and updates
- [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) - Build from source
- [RELEASE_NOTES_v0.1.1.md](RELEASE_NOTES_v0.1.1.md) - Detailed release notes
- [tests/README.md](tests/README.md) - Test suite documentation

---

## Testing

```bash
cd tests
python -m unittest test_conversion.py
```

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Author

Rose Scott ([@Snowman-scott](https://github.com/Snowman-scott))

---

## Contributing

Found a bug or have a feature request? [Open an issue](https://github.com/Snowman-scott/MicroBridge/issues).
