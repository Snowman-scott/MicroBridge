================================================================================
                         MicroBridge v0.1.1 - Release Package
================================================================================

Convert NDP.view2 annotations to Leica LMD format with ease.


WHAT'S INCLUDED
-------------------------------------------------------------------------------

This release contains two versions of MicroBridge:

  GUI Version  -  Interactive use, batch processing with visual feedback
  CLI Version  -  Scripting, automation, command-line workflows

Both versions produce identical output - choose based on your workflow.


QUICK START - GUI
-------------------------------------------------------------------------------

  1. Run MicroBridge_Setup_v0.1.1.exe
  2. Launch MicroBridge from Start Menu or Desktop
  3. Click "Select Files" or "Select Folder"
  4. Click "Start Conversion"
  5. Find output files with _LMD.xml suffix


QUICK START - CLI
-------------------------------------------------------------------------------

  1. Run MicroBridge_CLI_Setup_v0.1.1.exe
  2. Open Command Prompt or PowerShell
  3. Navigate to your annotation files
  4. Run: MicroBridge_CLI.exe *.ndpa

  Examples:
    MicroBridge_CLI.exe sample1.ndpa sample2.ndpa   (specific files)
    MicroBridge_CLI.exe                             (all NDPA in folder)
    MicroBridge_CLI.exe --help                      (show help)


ANNOTATION REQUIREMENTS
-------------------------------------------------------------------------------

Your annotation files must follow this structure:

  Regions 1-3  =  CALIBRATION POINTS (circle or freehand markers)
  Regions 4+   =  CAPTURE SHAPES (regions for microdissection)

Minimum 3 regions required. Additional regions become capture shapes.


SUPPORTED FORMATS
-------------------------------------------------------------------------------

  Input:   .ndpa (NDP.view2 XML)    -->    Output: _LMD.xml (Leica LMD)
  Input:   .csv  (NDP.view2 export) -->    Output: _LMD.xml (Leica LMD)

Note: CSV exports only contain centroid coordinates. Use NDPA for full
polygon data.


WHAT'S NEW IN v0.1.1
-------------------------------------------------------------------------------

  Reliability
    - Fixed calibration point extraction inconsistencies
    - Accurate ShapeCount in output files
    - Better error messages with actionable solutions

  Usability
    - Pre-flight validation catches errors early
    - Real-time progress for large files
    - Keyboard shortcuts (Ctrl+O, Ctrl+Q, Enter, Delete)

  Safety
    - Missing calibration data now fails by default (use --force to override)
    - Safe shutdown prevents corrupted files


TROUBLESHOOTING
-------------------------------------------------------------------------------

  "Need at least 3 regions"
    --> Add more annotations in NDP.view2

  "Calibration point missing coordinates"
    --> Check reference points have valid data in NDP.view2

  Permission denied
    --> Run as administrator or choose different output folder


LINKS
-------------------------------------------------------------------------------

  Source Code:      https://github.com/Snowman-scott/MicroBridge
  All Releases:     https://github.com/Snowman-scott/MicroBridge/releases
  Report Issues:    https://github.com/Snowman-scott/MicroBridge/issues
  Build from Src:   https://github.com/Snowman-scott/MicroBridge/blob/main/BUILD_INSTRUCTIONS.md


LICENSE
-------------------------------------------------------------------------------

MIT License - Free for personal and commercial use.


================================================================================
Author: Rose Scott (@Snowman-scott)
================================================================================
