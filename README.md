# MicroBridge
MicroBridge is a tool that allows file conversion between Slide annotation software like NDP.view2 to an XML format that Leica Microdissection (LMD) microscopes support.  

# Purpose
Scientists annotate regions of interest in Software like NDP.view2, They Would then have to re-draw those same annotations on the software for the LMDs.  
MicroBridge Takes the Annotation files from NDP.view2 and converts them into a format that the LMD can understand, This gives the scientists more time to do experiments rather than annotating files for the 2nd time.

## More will be added later :3

AGH DOCKS T_T

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
pip install -c .
```

# Usage
There are 2 ways to use MicroBridge
Option 1: Usage via the GUI (graphical user interface)
Install it first
and either run
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
pip install -c .
python run_tests.py
```
to set up the venv and run the tests

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
This project is licensed under the GNU GPLv3.0 License
This is important as it support copyleft! and Free software!

## More may be added later
