#!/usr/bin/env python3
"""
Unit tests for MicroBridge GUI NDPA conversion functions.
Tests the conversion logic WITHOUT requiring a display or Tkinter window.

The GUI class (MicroBridgeConverterApp) imports tkinter at module level and creates
a window in __init__. To test conversion logic headlessly, we mock tkinter before
importing the module, then use object.__new__() to skip __init__ entirely.

Run with: python -m unittest tests/test_gui_conversion.py -v
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
# Mock tkinter so MicroBridge_GUI can be imported without a display server
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

# Constants used at module level
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
    """Minimal StringVar stand-in that stores and returns values."""

    def __init__(self, value="", **kwargs):
        self._val = value

    def get(self):
        return self._val

    def set(self, v):
        self._val = v


_mock_tk.StringVar = _MockStringVar

# Sub-modules
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

# Now safe to import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "The_Source_Code"))
from MicroBridge_GUI import MicroBridgeConverterApp  # type: ignore[import]


def _make_headless_app(output_folder=""):
    """Create a MicroBridgeConverterApp instance without calling __init__."""
    app = object.__new__(MicroBridgeConverterApp)
    app.output_extension = ".xml"
    app.output_folder = _MockStringVar(output_folder)
    app.queue = queue.Queue()
    return app


class TestGUINDPAConversion(unittest.TestCase):
    """Test GUI NDPA conversion logic (headless)"""

    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
        self.temp_dir = tempfile.mkdtemp()
        self.app = _make_headless_app(self.temp_dir)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _parse_output(self, input_name):
        """Run conversion and parse the output XML."""
        input_file = os.path.join(self.test_data_dir, input_name)
        result = self.app.convert_ndpa_file(input_file)
        self.assertTrue(result, "Conversion should succeed for {}".format(input_name))

        base = os.path.splitext(input_name)[0]
        output_file = os.path.join(self.temp_dir, "{}_LMD.xml".format(base))
        self.assertTrue(os.path.exists(output_file), "Output file should exist")

        with open(output_file, "r", encoding="utf-8") as f:
            return minidom.parse(f)

    def _get_text(self, dom, tag):
        """Get text content of a tag from a DOM."""
        elem = dom.getElementsByTagName(tag)
        if not elem or not elem[0].firstChild:
            return None
        return elem[0].firstChild.data

    # --- Valid conversion ---

    def test_valid_ndpa_conversion(self):
        """Test GUI conversion of valid NDPA file with 3 calibration + 2 shapes"""
        dom = self._parse_output("valid_sample.ndpa")

        # Check structure
        self.assertEqual(len(dom.getElementsByTagName("ImageData")), 1)
        self.assertEqual(self._get_text(dom, "GlobalCoordinates"), "1")

        # Calibration values
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_1"), "100000")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_1"), "200000")
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_2"), "150000")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_2"), "250000")

        # Shape count
        self.assertEqual(self._get_text(dom, "ShapeCount"), "2")
        self.assertEqual(len(dom.getElementsByTagName("Shape_1")), 1)
        self.assertEqual(len(dom.getElementsByTagName("Shape_2")), 1)

    # --- Ruler skipping ---

    def test_ruler_annotation_skipped(self):
        """Test that ruler annotations are skipped in GUI conversion"""
        dom = self._parse_output("ruler_sample.ndpa")

        self.assertEqual(self._get_text(dom, "ShapeCount"), "2")
        self.assertEqual(len(dom.getElementsByTagName("Shape_1")), 1)
        self.assertEqual(len(dom.getElementsByTagName("Shape_2")), 1)

    def test_multiple_rulers_interleaved(self):
        """Test that multiple rulers interleaved with shapes are all skipped"""
        dom = self._parse_output("mixed_annotations.ndpa")

        self.assertEqual(self._get_text(dom, "ShapeCount"), "2")
        self.assertEqual(len(dom.getElementsByTagName("Shape_1")), 1)
        self.assertEqual(len(dom.getElementsByTagName("Shape_2")), 1)

    # --- Pointlist calibration fallback ---

    def test_pointlist_calibration_fallback(self):
        """Test calibration extraction via pointlist fallback in GUI"""
        dom = self._parse_output("pointlist_calibration.ndpa")

        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_1"), "100000")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_1"), "200000")
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_3"), "200000")
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_3"), "300000")

    # --- Missing calibration (no --force in GUI) ---

    def test_missing_calibration_fails(self):
        """Test that missing calibration data fails (GUI has no --force option)"""
        missing_file = os.path.join(self.temp_dir, "missing_cal.ndpa")
        with open(missing_file, "w", encoding="utf-8") as f:
            f.write("""<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <ndpviewstate id="1">
    <title>Cal_1</title>
    <annotation type="circle"><x>100000000</x><y>200000000</y></annotation>
  </ndpviewstate>
  <ndpviewstate id="2">
    <title>Cal_2_Missing</title>
  </ndpviewstate>
  <ndpviewstate id="3">
    <title>Cal_3</title>
    <annotation type="circle"><x>200000000</x><y>300000000</y></annotation>
  </ndpviewstate>
  <ndpviewstate id="4">
    <title>Shape_1</title>
    <annotation type="freehand"><pointlist><point><x>300000000</x><y>400000000</y></point></pointlist></annotation>
  </ndpviewstate>
</annotations>""")

        result = self.app.convert_ndpa_file(missing_file)
        self.assertFalse(result, "GUI should fail when calibration data is missing")

    # --- Insufficient regions ---

    def test_insufficient_regions(self):
        """Test that fewer than 3 regions fails"""
        insufficient_file = os.path.join(self.temp_dir, "insufficient.ndpa")
        with open(insufficient_file, "w", encoding="utf-8") as f:
            f.write("""<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <ndpviewstate id="1">
    <title>Cal_1</title>
    <annotation type="circle"><x>100000000</x><y>200000000</y></annotation>
  </ndpviewstate>
</annotations>""")

        result = self.app.convert_ndpa_file(insufficient_file)
        self.assertFalse(result, "Should fail with fewer than 3 regions")

    # --- Error handling ---

    def test_missing_file(self):
        """Test that a non-existent file returns False"""
        result = self.app.convert_ndpa_file("/nonexistent/path/file.ndpa")
        self.assertFalse(result)

    def test_invalid_xml(self):
        """Test that malformed XML returns False"""
        bad_file = os.path.join(self.temp_dir, "bad.ndpa")
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write("This is not valid XML <unclosed>tag")

        result = self.app.convert_ndpa_file(bad_file)
        self.assertFalse(result)

    # --- Coordinate conversion ---

    def test_coordinate_conversion_nm_to_um(self):
        """Test nm to um conversion (divide by 1000, round to int)"""
        dom = self._parse_output("valid_sample.ndpa")

        # 100000000 nm / 1000 = 100000 um
        self.assertEqual(self._get_text(dom, "X_CalibrationPoint_1"), "100000")
        # 250000000 nm / 1000 = 250000 um
        self.assertEqual(self._get_text(dom, "Y_CalibrationPoint_2"), "250000")

    # --- Output folder override ---

    def test_output_folder_override(self):
        """Test that setting output_folder writes there instead of input dir"""
        subfolder = os.path.join(self.temp_dir, "custom_output")
        os.makedirs(subfolder)
        self.app.output_folder.set(subfolder)

        input_file = os.path.join(self.test_data_dir, "valid_sample.ndpa")
        result = self.app.convert_ndpa_file(input_file)
        self.assertTrue(result)

        output_file = os.path.join(subfolder, "valid_sample_LMD.xml")
        self.assertTrue(
            os.path.exists(output_file), "Output should be in custom folder"
        )

    # --- Output file naming ---

    def test_output_file_naming(self):
        """Test that output uses _LMD.xml suffix"""
        input_file = os.path.join(self.test_data_dir, "valid_sample.ndpa")
        result = self.app.convert_ndpa_file(input_file)
        self.assertTrue(result)

        expected = os.path.join(self.temp_dir, "valid_sample_LMD.xml")
        self.assertTrue(os.path.exists(expected))

    # --- Region with no pointlist ---

    def test_shape_with_no_pointlist_is_skipped(self):
        """Test that a region without pointlist is skipped (no crash)"""
        no_pointlist_file = os.path.join(self.temp_dir, "no_pointlist.ndpa")
        with open(no_pointlist_file, "w", encoding="utf-8") as f:
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
    <title>Mystery_Region</title>
    <annotation type="circle"><x>500000000</x><y>600000000</y></annotation>
  </ndpviewstate>
  <ndpviewstate id="5">
    <title>Real_Shape</title>
    <annotation type="freehand"><pointlist><point><x>300000000</x><y>400000000</y></point><point><x>350000000</x><y>450000000</y></point></pointlist></annotation>
  </ndpviewstate>
</annotations>""")

        result = self.app.convert_ndpa_file(no_pointlist_file)
        self.assertTrue(result, "Should succeed, skipping region without pointlist")

        base = "no_pointlist"
        output_file = os.path.join(self.temp_dir, "{}_LMD.xml".format(base))
        with open(output_file, "r", encoding="utf-8") as f:
            dom = minidom.parse(f)

        # Only the real shape should appear
        self.assertEqual(self._get_text(dom, "ShapeCount"), "1")

    # --- _get_element_text helper ---

    def test_get_element_text_helper(self):
        """Test _get_element_text handles None, empty, and valid elements"""
        # None input
        self.assertEqual(self.app._get_element_text(None), "0")

        # Element with no children
        doc = minidom.parseString("<root><empty/></root>")
        empty_elem = doc.getElementsByTagName("empty")[0]
        self.assertEqual(self.app._get_element_text(empty_elem), "0")

        # Element with text
        doc = minidom.parseString("<root><val>12345</val></root>")
        val_elem = doc.getElementsByTagName("val")[0]
        self.assertEqual(self.app._get_element_text(val_elem), "12345")

        # Element with whitespace text
        doc = minidom.parseString("<root><val>  hello  </val></root>")
        val_elem = doc.getElementsByTagName("val")[0]
        self.assertEqual(self.app._get_element_text(val_elem), "hello")


def run_tests():
    """Run all GUI tests with verbose output"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGUINDPAConversion)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
