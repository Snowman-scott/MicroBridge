```zsh
 ___  ____               ______      _     _
 |  \/  (_)              | ___ \    (_)   | |
 | .  . |_  ___ _ __ ___ | |_/ /_ __ _  __| | __ _  ___
 | |\/| | |/ __| '__/ _ \| ___ \ '__| |/ _` |/ _` |/ _ \
 | |  | | | (__| | | (_) | |_/ / |  | | (_| | (_| |  __/
 \_|  |_/_|\___|_|  \___/\____/|_|  |_|\__,_|\__, |\___|
                                              __/ |
                                              |___/
```

---

MicroBridge is a tool that allows file conversion between Slide annotation software like NDP.view2 to an XML format that Leica Microdissection (LMD) microscopes support.

---

# Purpose
Scientists annotate regions of interest in software like NDP.view2, They would then have to re-draw those same annotations in the software for the LMDs.  
MicroBridge takes the annotation files from NDP.view2 and converts them into a format that the LMD can understand, This gives the scientists more time to do experiments rather than annotating files for the 2nd time.

---

# Installation

[![Packaging status](https://repology.org/badge/vertical-allrepos/microbridge-lmd.svg)](https://repology.org/project/microbridge-lmd/versions)

To install select your Operating system and follow one of the sets of instructions:
<details><summary><b>Linux</b></summary>
  
There is a universal way of installing MicroBridge on Linux

<details><summary>pipx</summary>
  
Make sure you have python installed, 
If you do not install python3.12 or above using your systems package manager.  

Then install pipx.
Then run:
```zsh
pipx install microbridge-lmd
```
  
If that does not work you can always overide it and run:
```zsh
pip install microbridge --break-system-packages
```
This will install it with normal pip but can cause issues with your system python.

</details><details><summary>AUR</summary>
  
Coming Soon!

</details>

I will hopefully get it onto more systems soon like debian (apt), fedora (dnf) and more (hopefully)

---

</details><details><summary><b>MacOS</b></summary>
  
There are 2 Main ways to Install MicroBridge on macOS

<details><summary>Homebrew(Brew)</summary>
  
Install [HomeBrew](https://docs.brew.sh/Installation) if not installed.

Run this in terminal:
```zsh
brew tap Snowman-scott/microbridge https://github.com/Snowman-scott/MicroBridge
brew trust Snowman-scott/microbridge
brew install microbridge-lmd
```

</details><details><summary>Binary Download</summary>
  
You can go to the [Releases page](https://github.com/Snowman-scott/MicroBridge/releases) and download the MB_MacOS_zip. (M Series processors Only!)  

**Note**: This won't allow you to type `microbridge` anywhere on your machine and run it CLI, The binary is only recommended if you plan on only using the GUI (User interface)  I recommend using the brew install above, pypi, or installing from source if you plan on using the CLI.

</details>

---

</details><details><summary><b>Windows</b></summary>
  
As of Current there is only one main way of installing MicroBridge on Windows

<details><summary>Binary Download</summary>
  
You can go to the [Releases page](https://github.com/Snowman-scott/MicroBridge/releases) and download the MB_Windows_zip. (x86_64)  

**Note**: This won't allow you to type `microbridge` anywhere on your machine and run it CLI, The binary is only recommended if you plan on only using the GUI (User interface)  I recommend using pypi, or installing from source if you plan on using the CLI.

</details><details><summary>Choco or Scoop</summary>
  
I may add these packages onto choco or scoop later on

</details>

---

</details><details><summary><b>pip & pipx<b></summary>
  
Using pip is not recommended on Linux unless you want to use a virtual environment,  I recommend linux and MacOS users to look in the Linux and macOS areas of this README for more appropriate installation.

<details><summary>pip</summary>
  
To install with pip make sure you have python installed  
Then run:
```zsh
pip install microbridge --break-system-packages
```

**Note:** I do not recommend Doing this on MacOS or Linux as it can break your system python

</details><details><summary>pipx</summary>
  
To install with pipx make sure you have python installed, 
If you do not have python installed then install python3.12 or above.
Then install pipx.

Then run:
```zsh
pipx install microbridge-lmd
```

</details>

---

</details><details><summary><b>Install from source</b></summary>

Make sure python 3.12 or above is installed.

You will also want git.

First Clone the Repo:
```zsh
git clone https://github.com/Snowman-scott/MicroBridge.git
```

Then move into the cloned dir:
```zsh
cd MicroBridge
```

Then Setup a venv:
```zsh
python3 -m .venv venv
```

Activate the vnev:
```zsh
source .venv/bin/activate
```

Then just install microbridge:
```zsh
pip install -e .
```

**Note:** This sets up MicroBridge in a virtual environment(venv), this means the code will only be able to be ran when you have that specific venv active.  I recommend Installing via pip or pipx if you plan to use this day to day, From source is preferred for development

</details></details>

---

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
pip install -e .[dev]
pytest
```
to set up the venv and run the tests (or use `python run_tests.py` for the summary table output)

---

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

---

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

---

# License
This project is licensed under the [GNU GPLv3.0 License](LICENSE)   
This is important as it support copyleft! and Free software!
