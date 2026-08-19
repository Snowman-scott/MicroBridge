# MicroBridge Test Suite

Automated tests for both the CLI and GUI converters. All tests use only the Python standard library -- no external dependencies required.

## Quick Start

Run **all** tests from the project root:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Test Files

| File | Tests | What it covers |
|------|-------|----------------|
| `test_conversion.py` | 18 | CLI NDPA conversion, batch conversion |
| `test_gui_conversion.py` | 13 | GUI NDPA conversion (headless, no window) |
| `test_csv_conversion.py` | 12 | GUI CSV conversion (headless, no window) |

**Total: 43 tests** (+ 1 skipped placeholder)

## Running Specific Tests

```bash
# Run only CLI tests
python -m unittest tests.test_conversion -v

# Run only GUI NDPA tests
python -m unittest tests.test_gui_conversion -v

# Run only CSV tests
python -m unittest tests.test_csv_conversion -v

# Run a specific test class
python -m unittest tests.test_conversion.TestBatchConversion -v

# Run a single test
python -m unittest tests.test_gui_conversion.TestGUINDPAConversion.test_ruler_annotation_skipped -v
```

## Test Data

Sample files in `test_data/`:

| File | Description |
|------|-------------|
| `valid_sample.ndpa` | 3 circle calibration points + 2 freehand shapes |
| `valid_sample.csv` | 3 calibration rows + 2 ROI rows (7 columns) |
| `ruler_sample.ndpa` | 3 calibration + 1 ruler (linearmeasure) + 2 shapes |
| `pointlist_calibration.ndpa` | Calibration via freehand pointlist (fallback path) |
| `mixed_annotations.ndpa` | 3 calibration + 2 rulers interleaved with 2 shapes |

Additional edge-case files (invalid XML, insufficient regions, etc.) are generated dynamically during tests.

## Test Coverage

### CLI Tests (`test_conversion.py`)

**NDPA Conversion:**
- Valid file conversion (3 cal + 2 shapes)
- Insufficient calibration points (<3 regions)
- Missing calibration coordinates (with and without `--force`)
- Missing input file
- Invalid/malformed XML
- Coordinate conversion (nm to um, divide by 1000)
- ShapeCount matches actual Shape elements
- Output file naming (`_LMD.xml` suffix)
- Ruler annotation skipping (single ruler)
- Multiple rulers interleaved with shapes
- Ruler-only file produces zero shapes
- Pointlist calibration fallback
- Empty annotations file

**Batch Conversion:**
- Directory with multiple valid files
- Empty directory
- Mix of valid and invalid files
- Ignores non-.ndpa files

### GUI NDPA Tests (`test_gui_conversion.py`)

- Valid file conversion with output structure validation
- Ruler annotation skipping (single and interleaved)
- Pointlist calibration fallback
- Missing calibration data fails (no `--force` in GUI)
- Insufficient regions
- Missing file and invalid XML error handling
- Coordinate nm-to-um conversion
- Output folder override
- Output file naming
- Region without pointlist is skipped
- `_get_element_text` helper method

### CSV Tests (`test_csv_conversion.py`)

- Valid CSV conversion with calibration and shapes
- Calibration extracted from correct columns (5, 6)
- Shapes are single-point (PointCount=1)
- Insufficient data rows
- Header-only file
- Empty file
- Missing columns default to 0
- Non-numeric coordinates default to 0
- Missing input file
- Large file (50 shapes)
- Output file naming
- Float coordinate rounding

## How GUI Tests Work (Headless)

The GUI class (`MicroBridgeConverterApp`) imports `tkinter` and creates a window in `__init__`. To test conversion logic without a display:

1. `tkinter` and its submodules are mocked before import using `unittest.mock`
2. Instances are created with `object.__new__()` to skip `__init__` entirely
3. Only the attributes needed by conversion methods are set manually (`output_folder`, `output_extension`, `queue`)

This means:
- Tests run in CI without `xvfb` or any display server
- No Tkinter window appears during testing
- Works identically on Windows, macOS, and Linux
- No external dependencies needed

## GitHub Actions CI

Tests run automatically on push to `main`/`dev` and on PRs to `main`.

**Matrix:** 3 operating systems x 5 Python versions = 15 combinations

| OS | Python Versions |
|----|----------------|
| Ubuntu | 3.9, 3.10, 3.11, 3.12, 3.13 |
| Windows | 3.9, 3.10, 3.11, 3.12, 3.13 |
| macOS | 3.9, 3.10, 3.11, 3.12, 3.13 |

No `pip install` step is needed since MicroBridge uses only the Python standard library.

The workflow file is at `.github/workflows/tests.yml`.

## Adding New Tests

1. Add your test method to the appropriate test class
2. Follow the naming convention: `test_description_of_what_is_tested`
3. Use descriptive assertion messages
4. Create test data files in `test_data/` if needed, or generate them dynamically
5. Clean up temporary files in `tearDown()`

For GUI tests, use the `_make_headless_app()` helper:

```python
def test_my_new_feature(self):
    """Test description"""
    app = _make_headless_app(self.temp_dir)
    result = app.convert_ndpa_file(input_path)
    self.assertTrue(result)
```

## Dependencies

Tests use only Python standard library:

- `unittest` -- test framework
- `unittest.mock` -- tkinter mocking for headless GUI tests
- `tempfile` -- temporary file handling
- `xml.dom.minidom` -- XML parsing for output validation
- `os`, `sys`, `shutil`, `queue`, `types` -- utilities

No additional packages required.
