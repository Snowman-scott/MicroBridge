# Plan for MicroBridge Development

## Notes
- Use a src/ 
- Add a pyproject.toml file for install
- Split the core code up from the CLI and GUI code
- Update the README.md file to include more information about the project, conversion types etc...
- Note that macOS does not come with tkinter by default 

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
    ├── test_core.py
    ├── test_gui.py
    └── test_cli.py
```

## CLI
- Click or argparse (probably click)
- Needs To have all the same features as the GUI
- Batch processing
- Clean easy to use

## GUI
- Customtkinter or Something else if i find something good?
- Probably allow PI to make it following my styling guide
- Design should look neat and nice not old and windows 95 like
- Should be easy to use, not have things burried in sub menus
