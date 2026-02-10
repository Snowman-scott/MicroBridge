#!/usr/bin/env python3
"""
Unit tests for MicroBridge CLI conversion functions.

Run with: python -m unittest tests/test_conversion.py
Or: python tests/test_conversion.py
"""

import os
import shutil
import sys
import tempfile
import unittest
from xml.dom import minidom

# Add parent directory to path to import MicroBridge modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "The_Source_Code"))
from MicroBridge_CLI import (  # type: ignore[import]
    batch_convert_directory,
    convert_ndpa_to_lmd,
)


class TestNDPAConversion(unittest.TestCase):
    """Test NDPA to LMD XML conversion"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_valid_ndpa_conversion(self):
        """Test conversion of valid NDPA file with 3 calibration + 2 shapes"""
        input_file = os.path.join(self.test_data_dir, "valid_sample.ndpa")
        output_file = os.path.join(self.temp_dir, "valid_sample_LMD.xml")

        # Perform conversion
        result = convert_ndpa_to_lmd(
            input_file, output_file, allow_missing_calibration=True
        )

        # Verify conversion succeeded
        self.assertTrue(result, "Conversion should succeed")
        self.assertTrue(os.path.exists(output_file), "Output file should be created")

        # Parse output and verify structure
        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # Check for required elements
        self.assertEqual(
            len(dom.getElementsByTagName("ImageData")), 1, "Should have ImageData root"
        )
        self.assertEqual(
            len(dom.getElementsByTagName("GlobalCoordinates")),
            1,
            "Should have GlobalCoordinates",
        )

        # Check calibration points
        self.assertEqual(
            len(dom.getElementsByTagName("X_CalibrationPoint_1")),
            1,
            "Should have CalibrationPoint_1 X",
        )
        self.assertEqual(
            len(dom.getElementsByTagName("Y_CalibrationPoint_1")),
            1,
            "Should have CalibrationPoint_1 Y",
        )
        self.assertEqual(
            len(dom.getElementsByTagName("X_CalibrationPoint_2")),
            1,
            "Should have CalibrationPoint_2 X",
        )
        self.assertEqual(
            len(dom.getElementsByTagName("Y_CalibrationPoint_2")),
            1,
            "Should have CalibrationPoint_2 Y",
        )
        self.assertEqual(
            len(dom.getElementsByTagName("X_CalibrationPoint_3")),
            1,
            "Should have CalibrationPoint_3 X",
        )
        self.assertEqual(
            len(dom.getElementsByTagName("Y_CalibrationPoint_3")),
            1,
            "Should have CalibrationPoint_3 Y",
        )

        # Check calibration point values (converted from nm to um)
        calib1_x_elem = dom.getElementsByTagName("X_CalibrationPoint_1")[0].firstChild
        calib1_y_elem = dom.getElementsByTagName("Y_CalibrationPoint_1")[0].firstChild
        assert calib1_x_elem is not None
        assert calib1_y_elem is not None
        calib1_x = getattr(calib1_x_elem, "data")
        calib1_y = getattr(calib1_y_elem, "data")
        self.assertEqual(calib1_x, "100000", "CalibrationPoint_1 X should be 100000 um")
        self.assertEqual(calib1_y, "200000", "CalibrationPoint_1 Y should be 200000 um")

        # Check ShapeCount
        shape_count_elem = dom.getElementsByTagName("ShapeCount")[0]
        shape_count_child = shape_count_elem.firstChild
        assert shape_count_child is not None
        shape_count = int(getattr(shape_count_child, "data"))
        self.assertEqual(shape_count, 2, "Should have 2 shapes")

        # Verify shapes exist
        self.assertEqual(
            len(dom.getElementsByTagName("Shape_1")), 1, "Should have Shape_1"
        )
        self.assertEqual(
            len(dom.getElementsByTagName("Shape_2")), 1, "Should have Shape_2"
        )

    def test_insufficient_calibration_points(self):
        """Test that files with <3 regions fail gracefully"""
        # Create a minimal NDPA with only 2 regions
        insufficient_file = os.path.join(self.temp_dir, "insufficient.ndpa")
        with open(insufficient_file, "w", encoding="utf-8") as f:
            f.write("""<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <ndpviewstate id="1">
    <title>Point1</title>
    <annotation type="circle">
      <x>100000000</x>
      <y>200000000</y>
    </annotation>
  </ndpviewstate>
  <ndpviewstate id="2">
    <title>Point2</title>
    <annotation type="circle">
      <x>150000000</x>
      <y>250000000</y>
    </annotation>
  </ndpviewstate>
</annotations>""")

        output_file = os.path.join(self.temp_dir, "insufficient_LMD.xml")
        result = convert_ndpa_to_lmd(insufficient_file, output_file)

        # Should fail due to insufficient calibration points
        self.assertFalse(result, "Conversion should fail with <3 regions")
        self.assertFalse(
            os.path.exists(output_file), "Output file should not be created"
        )

    def test_missing_calibration_coordinates(self):
        """Test handling of missing calibration point data"""
        # Create NDPA with empty calibration point
        missing_coords_file = os.path.join(self.temp_dir, "missing_coords.ndpa")
        with open(missing_coords_file, "w", encoding="utf-8") as f:
            f.write("""<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <ndpviewstate id="1">
    <title>Point1</title>
    <annotation type="circle">
      <x>100000000</x>
      <y>200000000</y>
    </annotation>
  </ndpviewstate>
  <ndpviewstate id="2">
    <title>Point2_Missing</title>
    <!-- Missing annotation element -->
  </ndpviewstate>
  <ndpviewstate id="3">
    <title>Point3</title>
    <annotation type="circle">
      <x>200000000</x>
      <y>300000000</y>
    </annotation>
  </ndpviewstate>
</annotations>""")

        output_file = os.path.join(self.temp_dir, "missing_coords_LMD.xml")

        # Without --force, should fail
        result = convert_ndpa_to_lmd(
            missing_coords_file, output_file, allow_missing_calibration=False
        )
        self.assertFalse(result, "Should fail without allow_missing_calibration flag")

        # With --force, should succeed but write placeholder
        result = convert_ndpa_to_lmd(
            missing_coords_file, output_file, allow_missing_calibration=True
        )
        self.assertTrue(result, "Should succeed with allow_missing_calibration=True")

        # Verify placeholder coordinates
        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        calib2_x_elem = dom.getElementsByTagName("X_CalibrationPoint_2")[0].firstChild
        calib2_y_elem = dom.getElementsByTagName("Y_CalibrationPoint_2")[0].firstChild
        assert calib2_x_elem is not None
        assert calib2_y_elem is not None
        calib2_x = getattr(calib2_x_elem, "data")
        calib2_y = getattr(calib2_y_elem, "data")
        self.assertEqual(calib2_x, "0", "Missing calibration X should be 0")
        self.assertEqual(calib2_y, "0", "Missing calibration Y should be 0")

    def test_missing_file(self):
        """Test error handling for non-existent input file"""
        result = convert_ndpa_to_lmd("nonexistent_file.ndpa")
        self.assertFalse(result, "Should fail for non-existent file")

    def test_invalid_xml(self):
        """Test handling of malformed XML"""
        invalid_xml_file = os.path.join(self.temp_dir, "invalid.ndpa")
        with open(invalid_xml_file, "w", encoding="utf-8") as f:
            f.write("This is not valid XML <unclosed>tag")

        output_file = os.path.join(self.temp_dir, "invalid_LMD.xml")
        result = convert_ndpa_to_lmd(invalid_xml_file, output_file)

        self.assertFalse(result, "Should fail for invalid XML")
        self.assertFalse(
            os.path.exists(output_file), "Output file should not be created"
        )

    def test_coordinate_conversion(self):
        """Test that coordinates are correctly converted from nanometers to micrometers"""
        input_file = os.path.join(self.test_data_dir, "valid_sample.ndpa")
        output_file = os.path.join(self.temp_dir, "coordinate_test_LMD.xml")

        result = convert_ndpa_to_lmd(
            input_file, output_file, allow_missing_calibration=True
        )
        self.assertTrue(result)

        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # Original: 100000000 nm = 100000 um
        calib1_x_elem = dom.getElementsByTagName("X_CalibrationPoint_1")[0].firstChild
        assert calib1_x_elem is not None
        calib1_x = int(getattr(calib1_x_elem, "data"))
        self.assertEqual(
            calib1_x, 100000, "Coordinate conversion should be correct (nm/1000 = um)"
        )

        # Original: 150000000 nm = 150000 um
        calib2_x_elem = dom.getElementsByTagName("X_CalibrationPoint_2")[0].firstChild
        assert calib2_x_elem is not None
        calib2_x = int(getattr(calib2_x_elem, "data"))
        self.assertEqual(
            calib2_x, 150000, "Coordinate conversion should divide by 1000"
        )

    def test_shape_count_matches_actual_shapes(self):
        """Test that ShapeCount matches the number of Shape elements written"""
        input_file = os.path.join(self.test_data_dir, "valid_sample.ndpa")
        output_file = os.path.join(self.temp_dir, "shape_count_test_LMD.xml")

        result = convert_ndpa_to_lmd(
            input_file, output_file, allow_missing_calibration=True
        )
        self.assertTrue(result)

        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # Get declared ShapeCount
        shape_count = int(
            getattr(dom.getElementsByTagName("ShapeCount")[0].firstChild, "data")
        )

        # Count actual Shape elements
        actual_shapes = len(
            [
                elem
                for elem in dom.getElementsByTagName("*")
                if elem.tagName.startswith("Shape_")
            ]
        )

        self.assertEqual(
            shape_count,
            actual_shapes,
            "Declared ShapeCount should match actual number of Shape elements",
        )

    def test_output_file_naming(self):
        """Test that output file naming is correct"""
        # Copy input file to temp dir to avoid writing to source tree
        original_file = os.path.join(self.test_data_dir, "valid_sample.ndpa")
        input_file = os.path.join(self.temp_dir, "valid_sample.ndpa")
        shutil.copy(original_file, input_file)

        # Don't specify output file - should auto-generate
        result = convert_ndpa_to_lmd(input_file, allow_missing_calibration=True)
        self.assertTrue(result)

        # Check that output file was created with correct name
        expected_output = os.path.join(self.temp_dir, "valid_sample_LMD.xml")
        self.assertTrue(
            os.path.exists(expected_output),
            "Output file should be created with _LMD.xml suffix",
        )

    # --- New tests: ruler skipping ---

    def test_ruler_annotation_skipped(self):
        """Test that ruler (linearmeasure) annotations are skipped during conversion"""
        input_file = os.path.join(self.test_data_dir, "ruler_sample.ndpa")
        output_file = os.path.join(self.temp_dir, "ruler_test_LMD.xml")

        result = convert_ndpa_to_lmd(input_file, output_file)
        self.assertTrue(result, "Conversion should succeed")

        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # Should have 2 shapes (ruler skipped)
        shape_count = int(
            getattr(dom.getElementsByTagName("ShapeCount")[0].firstChild, "data")
        )
        self.assertEqual(shape_count, 2, "ShapeCount should be 2 (ruler skipped)")

        # Verify shape numbering is sequential (1, 2 - no gaps)
        self.assertEqual(len(dom.getElementsByTagName("Shape_1")), 1)
        self.assertEqual(len(dom.getElementsByTagName("Shape_2")), 1)

    def test_multiple_rulers_skipped(self):
        """Test that multiple rulers interleaved with shapes are all skipped"""
        input_file = os.path.join(self.test_data_dir, "mixed_annotations.ndpa")
        output_file = os.path.join(self.temp_dir, "mixed_test_LMD.xml")

        result = convert_ndpa_to_lmd(input_file, output_file)
        self.assertTrue(result, "Conversion should succeed")

        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # Should have 2 shapes (both rulers skipped)
        shape_count = int(
            getattr(dom.getElementsByTagName("ShapeCount")[0].firstChild, "data")
        )
        self.assertEqual(shape_count, 2, "ShapeCount should be 2 (both rulers skipped)")

        # Verify sequential numbering
        self.assertEqual(len(dom.getElementsByTagName("Shape_1")), 1)
        self.assertEqual(len(dom.getElementsByTagName("Shape_2")), 1)

    def test_ruler_only_shapes_produces_zero_shapes(self):
        """Test that a file with only rulers (no real shapes) produces zero shapes"""
        ruler_only_file = os.path.join(self.temp_dir, "ruler_only.ndpa")
        with open(ruler_only_file, "w", encoding="utf-8") as f:
            f.write("""<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <ndpviewstate id="1">
    <title>Cal_1</title>
    <annotation type="circle"><x>100000000</x><y>200000000</y></annotation>
  </ndpviewstate>
  <ndpviewstate id="2">
    <title>Cal_2</title>
    <annotation type="circle"><x>150000000</x><y>250000000</y></annotation>
  </ndpviewstate>
  <ndpviewstate id="3">
    <title>Cal_3</title>
    <annotation type="circle"><x>200000000</x><y>300000000</y></annotation>
  </ndpviewstate>
  <ndpviewstate id="4">
    <title>Ruler_1</title>
    <annotation type="linearmeasure"><x1>100000000</x1><y1>100000000</y1><x2>200000000</x2><y2>200000000</y2></annotation>
  </ndpviewstate>
</annotations>""")

        output_file = os.path.join(self.temp_dir, "ruler_only_LMD.xml")
        result = convert_ndpa_to_lmd(ruler_only_file, output_file)
        self.assertTrue(result, "Conversion should succeed even with zero shapes")

        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        shape_count = int(
            getattr(dom.getElementsByTagName("ShapeCount")[0].firstChild, "data")
        )
        self.assertEqual(shape_count, 0, "ShapeCount should be 0")

    # --- New tests: pointlist fallback ---

    def test_pointlist_calibration_fallback(self):
        """Test calibration point extraction via pointlist fallback path"""
        input_file = os.path.join(self.test_data_dir, "pointlist_calibration.ndpa")
        output_file = os.path.join(self.temp_dir, "pointlist_cal_LMD.xml")

        result = convert_ndpa_to_lmd(input_file, output_file)
        self.assertTrue(result, "Conversion should succeed with pointlist calibration")

        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # Verify calibration values (100000000 nm / 1000 = 100000 um)
        calib1_x = getattr(
            dom.getElementsByTagName("X_CalibrationPoint_1")[0].firstChild, "data"
        )
        calib1_y = getattr(
            dom.getElementsByTagName("Y_CalibrationPoint_1")[0].firstChild, "data"
        )
        self.assertEqual(calib1_x, "100000")
        self.assertEqual(calib1_y, "200000")

    # --- New tests: edge cases ---

    def test_empty_annotation_file(self):
        """Test that an empty annotations file fails gracefully"""
        empty_file = os.path.join(self.temp_dir, "empty.ndpa")
        with open(empty_file, "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="utf-8"?>\n<annotations>\n</annotations>'
            )

        output_file = os.path.join(self.temp_dir, "empty_LMD.xml")
        result = convert_ndpa_to_lmd(empty_file, output_file)
        self.assertFalse(result, "Should fail with no regions")


class TestBatchConversion(unittest.TestCase):
    """Test batch directory conversion"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _copy_valid_sample(self, name):
        """Copy valid_sample.ndpa to temp_dir with a given name"""
        src = os.path.join(self.test_data_dir, "valid_sample.ndpa")
        dst = os.path.join(self.temp_dir, name)
        shutil.copy(src, dst)
        return dst

    def test_batch_convert_directory(self):
        """Test batch conversion of a directory with multiple valid files"""
        self._copy_valid_sample("file1.ndpa")
        self._copy_valid_sample("file2.ndpa")

        result = batch_convert_directory(self.temp_dir, allow_missing_calibration=True)
        self.assertEqual(result, 2, "Should convert 2 files successfully")

        # Verify output files exist
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "file1_LMD.xml")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "file2_LMD.xml")))

    def test_batch_convert_empty_directory(self):
        """Test batch conversion of an empty directory"""
        result = batch_convert_directory(self.temp_dir)
        self.assertEqual(result, 0, "Should return 0 for empty directory")

    def test_batch_convert_mixed_valid_invalid(self):
        """Test batch conversion with a mix of valid and invalid files"""
        self._copy_valid_sample("valid.ndpa")

        # Create an invalid NDPA file
        invalid_file = os.path.join(self.temp_dir, "invalid.ndpa")
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write("Not valid XML at all")

        result = batch_convert_directory(self.temp_dir, allow_missing_calibration=True)
        self.assertEqual(result, 1, "Should convert 1 of 2 files successfully")

    def test_batch_convert_ignores_non_ndpa(self):
        """Test that batch conversion ignores non-.ndpa files"""
        self._copy_valid_sample("real.ndpa")

        # Create non-ndpa files that should be ignored
        for name in ["readme.txt", "data.csv", "notes.md"]:
            with open(os.path.join(self.temp_dir, name), "w") as f:
                f.write("not an ndpa file")

        result = batch_convert_directory(self.temp_dir, allow_missing_calibration=True)
        self.assertEqual(result, 1, "Should only convert the .ndpa file")

        # Only one _LMD.xml should exist
        lmd_files = [f for f in os.listdir(self.temp_dir) if f.endswith("_LMD.xml")]
        self.assertEqual(len(lmd_files), 1)


class TestCSVConversion(unittest.TestCase):
    """Placeholder: CSV conversion is GUI-only. See test_csv_conversion.py."""

    @unittest.skip("CSV conversion is GUI-only; see tests/test_csv_conversion.py")
    def test_csv_basic_structure(self):
        pass


def run_tests():
    """Run all tests with verbose output"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestNDPAConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestBatchConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestCSVConversion))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code (0 = success, 1 = failure)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
