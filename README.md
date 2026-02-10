# MicroBridge

A conversion tool that bridges Hamamatsu's NDP.view2 digital slide annotation system with Leica Microdissection (LMD) microscopes. Converts `.ndpa` annotation files into LMD-compatible XML format.

## Purpose

Researchers annotate regions of interest in NDP.view2 and need to transfer those annotations to LMD systems for laser microdissection. MicroBridge automates this conversion, handling coordinate transformation, calibration point extraction, and batch processing.

## Features

- **GUI & CLI** - Graphical interface for interactive use, command-line for scripting
- **Batch Processing** - Convert entire folders at once
- **Multiple Formats** - Supports NDPA and CSV input files
- **Pre-flight Validation** - Catches errors before conversion starts
- **Ruler Skipping** - Ruler/measurement annotations are automatically ignored
- **Robust Error Handling** - Clear messages with actionable solutions

## Download

**[Latest Release (v0.1.1.1)](https://github.com/Snowman-scott/MicroBridge/releases/latest)**

- `MicroBridge_GUI.zip` - Graphical interface
- `MicroBridge_CLI.zip` - Command-line tool

## Run from Source

Requires Python 3.x (standard library only - no dependencies).

```bash
python The_Source_Code/MicroBridge_GUI.py
python The_Source_Code/MicroBridge_CLI.py [files...]
```

For building executables, see [BUILD_INSTRUCTIONS.md](Build_From_Source/BUILD_INSTRUCTIONS.md).

## Annotation Requirements

Your annotation files must follow this structure:

| Region # | Purpose |
|----------|---------|
| 1-3 | **Calibration Points** - Circle or freehand annotations |
| 4+ | **Capture Shapes** - Regions for microdissection |

Minimum 3 regions required. Both circle and freehand annotations work as calibration points.

Ruler annotations (linear measurements) are automatically skipped during conversion -- they won't affect your output or shape numbering.

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Need at least 3 regions" | Add more annotations as calibration points in NDP.view2 |
| "Calibration point missing coordinates" | Check reference points have valid data. Use `--force` flag in CLI to override (not recommended) |
| "Centroids only" warning | CSV exports lack polygon vertices - use NDPA format for full shape data |
| Permission errors | Check output folder permissions or run as administrator |

## Roadmap

**Planned**
- Context menu for file list (right-click to remove, open location)

**Under Consideration**
- Additional annotation format support
- macOS/Linux installers
- Drag-and-drop in GUI
- Recent files list
- Batch operation presets

## Development Story

This project started from a real need in digital pathology workflow. I wrote a simple proof-of-concept script to convert NDP.view2 annotations to LMD format, and it worked well enough for basic use. From there, I expanded the functionality, added the GUI for easier batch processing, and used AI assistance to polish the code, implement new features, and fix things I didn't know how to do myself.

It's been a practical learning experience - combining domain knowledge from my work with modern AI tools to build something genuinely useful.

## License

MIT License - See [LICENSE](LICENSE)

## Author

Rose Scott ([@Snowman-scott](https://github.com/Snowman-scott))

Found a bug? [Open an issue](https://github.com/Snowman-scott/MicroBridge/issues)

