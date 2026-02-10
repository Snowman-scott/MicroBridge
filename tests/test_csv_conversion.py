#!/usr/bin/env python3
"""
Unit tests for MicroBridge GUI CSV conversion functions.
Tests the CSV-to-LMD conversion logic WITHOUT requiring a display or Tkinter window.

Run with: python -m unittest tests/test_csv_conversion.py -v
"""

import os
import queue
import shutil
import sys
import tempfile
import types
import unittest
import unittest.mock
from xml.dom import minidom

# ---------------------------------------------------------------------------
# Mock tkinter (same approach as test_gui_conversion.py)
# ---------------------------------------------------------------------------
_mock_tk = types.ModuleType("tkinter")
for _attr in [
    "Tk",
    "Frame",
    "Label",
    "Button",
    "Listbox",
    "Radiobutton",
    "LabelFrame",
    "Scrollbar",
]:
    setattr(_mock_tk, _attr, unittest.mock.MagicMock())

for _const in [
    "END",
    "NORMAL",
    "DISABLED",
    "EXTENDED",
    "VERTICAL",
    "X",
    "Y",
    "BOTH",
    "LEFT",
    "RIGHT",
    "TOP",
    "BOTTOM",
    "W",
    "NW",
]:
    setattr(_mock_tk, _const, _const.lower())


class _MockStringVar:
    def __init__(self, value="", **kwargs):
        self._val = value

    def get(self):
        return self._val

    def set(self, v):
        self._val = v


_mock_tk.StringVar = _MockStringVar

for _submod in [
    "tkinter.filedialog",
    "tkinter.messagebox",
    "tkinter.scrolledtext",
    "tkinter.ttk",
]:
    sys.modules[_submod] = types.ModuleType(_submod)
sys.modules["tkinter.ttk"].Progressbar = unittest.mock.MagicMock()
sys.modules["tkinter.ttk"].Style = unittest.mock.MagicMock()
sys.modules["tkinter.scrolledtext"].ScrolledText = unittest.mock.MagicMock()
sys.modules["tkinter"] = _mock_tk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "The_Source_Code"))
from MicroBridge_GUI import MicroBridgeConverterApp  # type: ignore[import]


def _make_headless_app(output_folder=""):
    """Create a MicroBridgeConverterApp instance without calling __init__."""
    app = object.__new__(MicroBridgeConverterApp)
    app.output_extension = ".xml"
    app.output_folder = _MockStringVar(output_folder)
    app.queue = queue.Queue()
    return app


class TestCSVConversion(unittest.TestCase):
    """Test GUI CSV conversion logic (headless)"""

    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
        self.temp_dir = tempfile.mkdtemp()
        self.app = _make_headless_app(self.temp_dir)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _write_csv(self, name, lines):
        """Write a CSV file to temp_dir and return the path."""
        path = os.path.join(self.temp_dir, name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            for line in lines:
                f.write(line + "\n")
        return path

    def _get_text(self, dom, tag):
        """Get text content of a tag from a DOM."""
        elem = dom.getElementsByTagName(tag)
        if not elem or not elem[0].firstChild:
            return None
        return elem[0].firstChild.data

    # --- Valid CSV conversion ---

    def test_valid_csv_conversion(self):
        """Test conversion of valid CSV with 3 calibration + 2 shapes"""
        input_file = os.path.join(self.test_data_dir, "valid_sample.csv")
        result = self.app.convert_csv_file(input_file)
        self.assertTrue(result, "Conversion should succeed")

        output_file = os.path.join(self.temp_dir, "valid_sample_LMD.xml")
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # Structure
        self.assertEqual(len(dom.getElementsByTagName("ImageData")), 1)
        self.assertEqual(self._get_text(dom, "GlobalCoordinates"), "1")

        # Calibration
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_1"), "100")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_1"), "200")
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_2"), "150")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_2"), "250")
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_3"), "200")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_3"), "300")

        # Shapes
        self.assertEqual(self._get_text(dom, "ShapeCount"), "2")

    def test_csv_calibration_values(self):
        """Test that calibration is extracted from columns 5 and 6 (0-indexed)"""
        csv_file = self._write_csv(
            "cal_test.csv",
            [
                "A,B,C,D,E,X,Y",
                "1,2,3,4,5,111,222",
                "1,2,3,4,5,333,444",
                "1,2,3,4,5,555,666",
            ],
        )

        result = self.app.convert_csv_file(csv_file)
        self.assertTrue(result)

        output_file = os.path.join(self.temp_dir, "cal_test_LMD.xml")
        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_1"), "111")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_1"), "222")
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_2"), "333")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_2"), "444")

    def test_csv_shape_is_single_point(self):
        """Test that each CSV shape has PointCount=1 with one X/Y pair"""
        input_file = os.path.join(self.test_data_dir, "valid_sample.csv")
        result = self.app.convert_csv_file(input_file)
        self.assertTrue(result)

        output_file = os.path.join(self.temp_dir, "valid_sample_LMD.xml")
        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # Each shape should have PointCount=1
        point_counts = dom.getElementsByTagName("PointCount")
        for pc in point_counts:
            self.assertEqual(
                pc.firstChild.data, "1", "CSV shapes should be single-point"
            )

    # --- Insufficient data ---

    def test_csv_insufficient_rows(self):
        """Test that CSV with fewer than 3 data rows fails"""
        csv_file = self._write_csv(
            "short.csv",
            [
                "A,B,C,D,E,X,Y",
                "1,2,3,4,5,100,200",
                "1,2,3,4,5,150,250",
            ],
        )

        result = self.app.convert_csv_file(csv_file)
        self.assertFalse(result, "Should fail with only 2 data rows")

    def test_csv_header_only(self):
        """Test that CSV with only a header row fails"""
        csv_file = self._write_csv(
            "header_only.csv",
            [
                "A,B,C,D,E,X,Y",
            ],
        )

        result = self.app.convert_csv_file(csv_file)
        self.assertFalse(result, "Should fail with only header row")

    def test_csv_empty_file(self):
        """Test that a completely empty CSV file fails"""
        csv_file = self._write_csv("empty.csv", [])

        result = self.app.convert_csv_file(csv_file)
        self.assertFalse(result, "Should fail for empty file")

    # --- Edge cases: bad data ---

    def test_csv_missing_columns(self):
        """Test that rows with fewer than 7 columns default to 0"""
        csv_file = self._write_csv(
            "short_cols.csv",
            [
                "A,B,C,D,E,X,Y",
                "1,2,3",  # only 3 columns
                "1,2,3,4",  # only 4 columns
                "1,2,3,4,5",  # only 5 columns
                "1,2,3,4,5,999,888",  # valid shape row
            ],
        )

        result = self.app.convert_csv_file(csv_file)
        self.assertTrue(result, "Should succeed, defaulting missing columns to 0")

        output_file = os.path.join(self.temp_dir, "short_cols_LMD.xml")
        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # First 3 calibration points should default to 0
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_1"), "0")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_1"), "0")

    def test_csv_non_numeric_coordinates(self):
        """Test that non-numeric X/Y values default to 0"""
        csv_file = self._write_csv(
            "bad_nums.csv",
            [
                "A,B,C,D,E,X,Y",
                "1,2,3,4,5,abc,def",
                "1,2,3,4,5,100,200",
                "1,2,3,4,5,150,250",
            ],
        )

        result = self.app.convert_csv_file(csv_file)
        self.assertTrue(result, "Should succeed, defaulting bad numbers to 0")

        output_file = os.path.join(self.temp_dir, "bad_nums_LMD.xml")
        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # First calibration point should be 0 (non-numeric input)
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_1"), "0")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_1"), "0")
        # Second should be valid
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_2"), "100")

    # --- Error handling ---

    def test_csv_missing_file(self):
        """Test that a non-existent CSV file returns False"""
        result = self.app.convert_csv_file("/nonexistent/path/file.csv")
        self.assertFalse(result)

    # --- Large file ---

    def test_csv_large_file(self):
        """Test conversion of a CSV with 50 shape rows"""
        lines = ["Region,ID,Type,Name,Color,X,Y"]
        # 3 calibration rows
        for i in range(3):
            lines.append(
                "{},,Point,Cal_{},Red,{},{}".format(
                    i + 1, i + 1, (i + 1) * 100, (i + 1) * 200
                )
            )
        # 50 shape rows
        for i in range(50):
            lines.append(
                "{},,ROI,ROI_{},Blue,{},{}".format(i + 4, i + 1, 1000 + i, 2000 + i)
            )

        csv_file = self._write_csv("large.csv", lines)
        result = self.app.convert_csv_file(csv_file)
        self.assertTrue(result)

        output_file = os.path.join(self.temp_dir, "large_LMD.xml")
        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        self.assertEqual(self._get_text(dom, "ShapeCount"), "50")

    # --- Output naming ---

    def test_csv_output_naming(self):
        """Test that CSV output uses _LMD.xml suffix"""
        input_file = os.path.join(self.test_data_dir, "valid_sample.csv")
        result = self.app.convert_csv_file(input_file)
        self.assertTrue(result)

        expected = os.path.join(self.temp_dir, "valid_sample_LMD.xml")
        self.assertTrue(os.path.exists(expected))

    # --- Float rounding ---

    def test_csv_float_coordinate_rounding(self):
        """Test that float coordinates are rounded to nearest integer"""
        csv_file = self._write_csv(
            "floats.csv",
            [
                "A,B,C,D,E,X,Y",
                "1,2,3,4,5,100.6,200.4",
                "1,2,3,4,5,150.5,250.5",
                "1,2,3,4,5,200.1,300.9",
            ],
        )

        result = self.app.convert_csv_file(csv_file)
        self.assertTrue(result)

        output_file = os.path.join(self.temp_dir, "floats_LMD.xml")
        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # 100.6 -> 101, 200.4 -> 200
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_1"), "101")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_1"), "200")


def run_tests():
    """Run all CSV tests with verbose output"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCSVConversion)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
