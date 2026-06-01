# MicroBridge

A conversion tool that bridges Hamamatsu's NDP.view2 digital slide annotation system with Leica Microdissection (LMD) microscopes. Converts `.ndpa` annotation files into LMD-compatible XML format.

# NOTICE!
## Main development of Microbridge will be moving over to GitLab!  
A mirror will still be pushed here But please DO NOT make or push any code to this REPO!  
Thanks, Rose :3

## Purpose

Researchers annotate regions of interest in NDP.view2 and need to transfer those annotations to LMD systems for laser microdissection. MicroBridge automates this conversion, handling coordinate transformation, calibration point extraction, and batch processing.

---
## 🚀 What's New in v1.2.0
We've completely overhauled the engine to be more robust and easier to use:
- **Unified Binary**: One executable for everything. Double-click for the GUI, or use `--cli` in a terminal.
- **Cross-Platform Verified**: Automatically tested on **Windows, macOS, and Linux (Debian, Arch, Fedora)**.
- **Python 3.14 Ready**: Support for the latest Python environments.
- **Smart Filtering**: "Ruler" measurements are now automatically ignored so they don't mess up your laser shapes.

## Features

- **GUI & CLI** - Graphical interface for interactive use, command-line for scripting
- **Batch Processing** - Convert entire folders at once
- **Multiple Formats** - Supports NDPA and CSV input files
- **Pre-flight Validation** - Catches errors before conversion starts
- **Ruler Skipping** - Ruler/measurement annotations are automatically ignored
- **Robust Error Handling** - Clear messages with actionable solutions

## Download

**[Latest Release (v1.2.0)](https://github.com/Snowman-scott/MicroBridge/releases/latest)**

- `MicroBridge.zip` - Graphical interface & CLI Tool (More info below)

## Running MicroBridge in its 2 different modes
When users want to use the **Graphical user interface**: \
All you have to do is run the `MicroBridge.exe` file Normally Via Double clicking the icon

When you want to use the **CLI Tool**: \
Open terminal, wherever the `MicroBridge.exe` is and run:
```
MicroBridge.exe --cli
```

## Run from Source

Requires Python 3.9 - 3.14 (standard library only - no dependencies).

```bash
python The_Source_Code/MicroBridge.py
# Or for the CLI
python The_Source_Code/MicroBridge.py --cli
```

For building executables, see [BUILD_INSTRUCTIONS.md](Build_From_Source/BUILD_INSTRUCTIONS.md).

## Workflow

**NDPI -> NDPA (Annotation file) -> MicroBridge -> LMD XML**

## Annotation Requirements

Your annotation files must follow this structure:

| Region # | Purpose |
|----------|---------|
| 1-3 | **Calibration Points** - Circle or freehand annotations |
| 4+ | **Capture Shapes** - Regions for microdissection |

Minimum 3 regions required. Both circle and freehand annotations work as calibration points. **But Circle annotations are preferred**

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
- macOS and Linux native packages
- Xenium annotation conversion support
- Omero support

**Under Consideration**
- Context menu for file list (right-click to remove, open location)
- Additional annotation format support
- Drag-and-drop in GUI
- Recent files list
- Batch operation presets
- Images and gifs in README.md
- Basic QuickStart Guide

## Development Story

This project started from a real need in digital pathology workflow. I wrote a simple proof-of-concept script to convert NDP.view2 annotations to LMD format, and it worked well enough for basic use. From there, I expanded the functionality, added the GUI for easier batch processing, and used AI assistance to polish the code, implement new features, and fix things I didn't know how to do myself.

It's been a practical learning experience - combining domain knowledge from my work with modern AI tools to build something genuinely useful.

## License

This project is Licensed under The **GNU GENERAL PUBLIC LICENSE V3** (GPL-3.0)

## Author

Rose Scott ([@Snowman-scott](https://github.com/Snowman-scott))

Found a bug? [Open an issue](https://github.com/Snowman-scott/MicroBridge/issues)
