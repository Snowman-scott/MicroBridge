# MicroBridge Unit Tests

This directory contains unit tests for MicroBridge conversion functions.

## Running Tests

### Run All Tests

```bash
# From project root
python -m unittest tests/test_conversion.py

# Or directly
python tests/test_conversion.py
```

### Run Specific Test Class

```bash
python -m unittest tests.test_conversion.TestNDPAConversion
```

### Run Specific Test

```bash
python -m unittest tests.test_conversion.TestNDPAConversion.test_valid_ndpa_conversion
```

### Run with Verbose Output

```bash
python -m unittest tests/test_conversion.py -v
```

## Test Coverage

### NDPA Conversion Tests

- ✅ **test_valid_ndpa_conversion** - Tests successful conversion with 3 calibration points + 2 shapes
- ✅ **test_insufficient_calibration_points** - Verifies failure when <3 regions exist
- ✅ **test_missing_calibration_coordinates** - Tests placeholder handling with `--force` flag
- ✅ **test_missing_file** - Tests error handling for non-existent files
- ✅ **test_invalid_xml** - Tests handling of malformed XML
- ✅ **test_coordinate_conversion** - Verifies nm → μm conversion (÷1000)
- ✅ **test_shape_count_matches_actual_shapes** - Ensures ShapeCount accuracy
- ✅ **test_output_file_naming** - Verifies `_LMD.xml` suffix is applied

### CSV Conversion Tests

- 🔄 **Placeholder** - CSV tests to be implemented when needed

## Test Data

Sample files in `test_data/`:

- **valid_sample.ndpa** - Valid NDPA file with 3 calibration points (circles) + 2 capture shapes (freehand)
- **valid_sample.csv** - Valid CSV file with 3 calibration points + 2 ROIs

Additional test files are generated dynamically during tests for edge cases.

## Test Results

Expected output:
```
test_coordinate_conversion (__main__.TestNDPAConversion) ... ok
test_insufficient_calibration_points (__main__.TestNDPAConversion) ... ok
test_invalid_xml (__main__.TestNDPAConversion) ... ok
test_missing_calibration_coordinates (__main__.TestNDPAConversion) ... ok
test_missing_file (__main__.TestNDPAConversion) ... ok
test_output_file_naming (__main__.TestNDPAConversion) ... ok
test_shape_count_matches_actual_shapes (__main__.TestNDPAConversion) ... ok
test_valid_ndpa_conversion (__main__.TestNDPAConversion) ... ok

----------------------------------------------------------------------
Ran 8 tests in X.XXXs

OK
```

## Adding New Tests

1. Add test method to appropriate test class in `test_conversion.py`
2. Follow naming convention: `test_description_of_what_is_tested`
3. Use descriptive assertion messages
4. Create test data files in `test_data/` if needed
5. Clean up temporary files in `tearDown()`

Example:
```python
def test_my_new_feature(self):
    """Test description"""
    # Setup
    input_file = os.path.join(self.test_data_dir, 'my_test.ndpa')
    output_file = os.path.join(self.temp_dir, 'output.xml')
    
    # Execute
    result = convert_ndpa_to_lmd(input_file, output_file)
    
    # Verify
    self.assertTrue(result, "Conversion should succeed")
    self.assertTrue(os.path.exists(output_file), "Output should be created")
```

## Continuous Integration

To run tests automatically in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run unit tests
  run: python -m unittest discover tests/
```

## Dependencies

Tests use only Python standard library:
- `unittest` - Test framework
- `tempfile` - Temporary file handling
- `xml.dom.minidom` - XML parsing for validation
- `os`, `sys`, `shutil` - File operations

No additional dependencies required!
