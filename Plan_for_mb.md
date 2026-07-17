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
