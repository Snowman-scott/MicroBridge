# MicroBridge
MicroBridge is a tool that allows file conversion between Slide annotation software like NDP.view2 to an XML format that Leica Microdissection (LMD) microscopes support.  

# Purpose
Scientists annotate regions of interest in software like NDP.view2, They would then have to re-draw those same annotations in the software for the LMDs.  
MicroBridge takes the annotation files from NDP.view2 and converts them into a format that the LMD can understand, This gives the scientists more time to do experiments rather than annotating files for the 2nd time.

# Installation
To install the package do one of the following:

A. Grab the release from the release section
(Mainly for windows)

B. Clone the Repo
Make a virtual environment
```zsh
python3 -m venv .venv
```
Then:
```zsh
pip install -e .
```

# Usage
There are 2 ways to use MicroBridge
Option 1: Usage via the GUI (graphical user interface)
Install it first
And either run
```zsh
microbridge
```
In your terminal and it will open up
Or use the desktop icon / entry to open the program

Option 2: Usage via the terminal
For typical usage you would run
```zsh
microbridge filename.ndpa file2.ndpa file3.ndpa ...
```
There are 2 flags that you can use to help with input and output
Flag 1: Batch processing 
To process a whole folder / directory run
```zsh
microbridge -b directory-path
```
Flag 2: output dir
To set a specific directory / folder for the files be placed into run
```zsh
microbridge filename.ndpa -o 'path/to/dir'
```

You can use both flags with each other
```zsh
microbridge -b 'path/to/.ndpa/dir' -o 'path/to/output/dir'
```

You can also run 
```zsh
microbridge --help
```
This shows you all the commands and a quick run down of what they do

---
# Tests
There is information about running the tests locally in the tests directory of the REPO

You can run this
```zsh
python -m venv .venv
source .venv/bin/activate
pip install -e .
python run_tests.py
```
to set up the venv and run the tests

## ndpa -> LMD(xml) example
A raw ndpa looks like this:
```xml
<!-- Calibration Point 3 - Circle annotation -->
<ndpviewstate id="3">
  <title>Calibration_3</title>
  <annotation type="circle">
    <x>200000000</x>
    <y>300000000</y>
    <radius>5000000</radius>
  </annotation>
</ndpviewstate>

<!-- RULER - should be SKIPPED -->
<ndpviewstate id="4">
  <title>Measurement_1</title>
  <annotation type="linearmeasure" displayname="AnnotateRuler" color="#ff0000">
    <x1>100000000</x1>
    <y1>100000000</y1>
    <x2>200000000</x2>
    <y2>200000000</y2>
  </annotation>
</ndpviewstate>
```
MicroBridge (currently) converts this to an XML for the LMD's which look like this:
```xml
  <X_CalibrationPoint_3>200000</X_CalibrationPoint_3>
  <Y_CalibrationPoint_3>300000</Y_CalibrationPoint_3>
  <ShapeCount>2</ShapeCount>
  <Shape_1>
    <PointCount>3</PointCount>
    <X_1>300000</X_1>
    <Y_1>400000</Y_1>
    <X_2>350000</X_2>
    <Y_2>400000</Y_2>
    <X_3>350000</X_3>
    <Y_3>450000</Y_3>
  </Shape_1>
```
This example above is cut down for length reasons

If you want to see a real world example and the full example above you can look here:
[ndpa --> LMD(xml) examples](ndpa_to_LMD_examples/)

## Codebase Layout
```
src/
    ├── MicroBridge/
    │   ├── __init__.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── conversion.py
    │   │   └── utils.py
    │   ├── cli/
    │   │   ├── __init__.py
    │   │   └── main.py
    │   └── gui/
    │       ├── __init__.py
    │       └── main.py
tests/
    ├── __init__.py
    ├── README.md
    ├── test_core.py
    ├── test_gui.py
    ├── test_intergration.py
    ├── test_utils.py
    ├── test_cli.py
    └── test_Data/
        └── All the test data, I am not writing that out...
        
pyproject.toml
run_tests.py

```

# License
This project is licensed under the [GNU GPLv3.0 License](LICENSE)
This is important as it support copyleft! and Free software!
