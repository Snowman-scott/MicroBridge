#!/usr/bin/env python3
"""
Unit tests for MicroBridge conversion functions.

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
from MicroBridge_CLI import convert_ndpa_to_lmd  # type: ignore[import]


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
        input_file = os.path.join(self.test_data_dir, "valid_sample.ndpa")

        # Don't specify output file - should auto-generate
        result = convert_ndpa_to_lmd(input_file, allow_missing_calibration=True)
        self.assertTrue(result)

        # Check that output file was created with correct name
        expected_output = os.path.join(self.test_data_dir, "valid_sample_LMD.xml")
        self.assertTrue(
            os.path.exists(expected_output),
            "Output file should be created with _LMD.xml suffix",
        )

        # Clean up
        if os.path.exists(expected_output):
            os.remove(expected_output)


class TestCSVConversion(unittest.TestCase):
    """Test CSV to LMD XML conversion"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_csv_basic_structure(self):
        """Test that CSV conversion creates valid LMD XML structure"""
        # Note: CSV conversion would need to be implemented separately
        # This is a placeholder for when CSV conversion is added to CLI
        pass


def run_tests():
    """Run all tests with verbose output"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestNDPAConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestCSVConversion))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code (0 = success, 1 = failure)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
