import unittest
import tempfile
import shutil
from pathlib import Path
from xml.dom import minidom

from MicroBridge.Core.core import derive_output_filename, convert_ndpa_to_lmd_core


class TestDeriveOutputFilename(unittest.TestCase):
    def test_appends_lmd_xml_suffix(self):
        result = derive_output_filename("/data/sample.ndpa")
        self.assertEqual(result, "/data/sample_LMD.xml")

    def test_handles_file_without_extension(self):
        result = derive_output_filename("/data/sample")
        self.assertEqual(result, "/data/sample_LMD.xml")

    def test_keeps_different_directory(self):
        result = derive_output_filename("/some/other/path/foo.ndpa")
        self.assertEqual(result, "/some/other/path/foo_LMD.xml")


class TestConvertNdpaToLmdCore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_input(self, name: str, xml: str) -> str:
        p = Path(self.tmp) / name
        p.write_text(xml, encoding="utf-8")
        return str(p)

    def _convert(self, input_name: str, xml: str) -> minidom.Document:
        in_path = self._write_input(input_name, xml)
        out_path = str(Path(self.tmp) / f"{Path(input_name).stem}_LMD.xml")
        convert_ndpa_to_lmd_core(in_path, out_path)
        return minidom.parse(out_path)

    def _text(self, dom, tag: str) -> str | None:
        els = dom.getElementsByTagName(tag)
        if not els or not els[0].firstChild:
            return None
        return els[0].firstChild.data

    # ── happy path ────────────────────────────────────────

    def test_converts_valid_ndpa(self):
        dom = self._convert("test.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist>
      <point><x>300000000</x><y>400000000</y></point>
      <point><x>350000000</x><y>450000000</y></point>
    </pointlist>
  </annotation></ndpviewstate>
</annotations>""")
        self.assertEqual(self._text(dom, "GlobalCoordinates"), "1")
        self.assertEqual(self._text(dom, "X_CalibrationPoint_1"), "100000")
        self.assertEqual(self._text(dom, "Y_CalibrationPoint_1"), "200000")
        self.assertEqual(self._text(dom, "ShapeCount"), "1")

    def test_output_xml_structure_has_all_expected_elements(self):
        dom = self._convert("struct.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>300000000</x><y>400000000</y></point></pointlist>
  </annotation></ndpviewstate>
</annotations>""")
        self.assertEqual(len(dom.getElementsByTagName("ImageData")), 1)
        self.assertEqual(len(dom.getElementsByTagName("GlobalCoordinates")), 1)
        for i in range(1, 4):
            self.assertEqual(len(dom.getElementsByTagName(f"X_CalibrationPoint_{i}")), 1)
            self.assertEqual(len(dom.getElementsByTagName(f"Y_CalibrationPoint_{i}")), 1)
        self.assertEqual(len(dom.getElementsByTagName("ShapeCount")), 1)
        self.assertEqual(len(dom.getElementsByTagName("Shape_1")), 1)

    def test_calibration_extracted_via_annotation_method(self):
        dom = self._convert("cal_annot.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>50000000</x><y>75000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>125000000</x><y>175000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
</annotations>""")
        self.assertEqual(self._text(dom, "X_CalibrationPoint_1"), "50000")
        self.assertEqual(self._text(dom, "Y_CalibrationPoint_1"), "75000")
        self.assertEqual(self._text(dom, "X_CalibrationPoint_2"), "125000")
        self.assertEqual(self._text(dom, "Y_CalibrationPoint_2"), "175000")
        self.assertEqual(self._text(dom, "X_CalibrationPoint_3"), "200000")
        self.assertEqual(self._text(dom, "Y_CalibrationPoint_3"), "300000")

    def test_calibration_via_pointlist_fallback_when_annotation_missing(self):
        dom = self._convert("cal_pointlist.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate>
    <annotation type="freehand"><pointlist><point><x>100000000</x><y>200000000</y></point></pointlist></annotation>
  </ndpviewstate>
  <ndpviewstate>
    <annotation type="freehand"><pointlist><point><x>150000000</x><y>250000000</y></point></pointlist></annotation>
  </ndpviewstate>
  <ndpviewstate>
    <annotation type="freehand"><pointlist><point><x>200000000</x><y>300000000</y></point></pointlist></annotation>
  </ndpviewstate>
</annotations>""")
        self.assertEqual(self._text(dom, "X_CalibrationPoint_1"), "100000")
        self.assertEqual(self._text(dom, "Y_CalibrationPoint_1"), "200000")

    def test_calibration_pointlist_fallback_when_annotation_has_no_xy(self):
        dom = self._convert("cal_annot_no_xy.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate>
    <annotation type="circle"><radius>5000</radius></annotation>
    <annotation type="freehand"><pointlist><point><x>100000000</x><y>200000000</y></point></pointlist></annotation>
  </ndpviewstate>
  <ndpviewstate>
    <annotation type="circle"><radius>5000</radius></annotation>
    <annotation type="freehand"><pointlist><point><x>150000000</x><y>250000000</y></point></pointlist></annotation>
  </ndpviewstate>
  <ndpviewstate>
    <annotation type="circle"><radius>5000</radius></annotation>
    <annotation type="freehand"><pointlist><point><x>200000000</x><y>300000000</y></point></pointlist></annotation>
  </ndpviewstate>
</annotations>""")
        self.assertEqual(self._text(dom, "X_CalibrationPoint_1"), "100000")
        self.assertEqual(self._text(dom, "Y_CalibrationPoint_1"), "200000")

    # ── shape extraction ──────────────────────────────────

    def test_ruler_annotation_skipped(self):
        dom = self._convert("ruler.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="linearmeasure"><x1>100</x1><y1>100</y1></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>300000000</x><y>400000000</y></point></pointlist>
  </annotation></ndpviewstate>
</annotations>""")
        self.assertEqual(self._text(dom, "ShapeCount"), "1")

    def test_only_rulers_produces_zero_shapes(self):
        dom = self._convert("ruler_only.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="linearmeasure"><x1>100</x1><y1>100</y1></annotation></ndpviewstate>
  <ndpviewstate><annotation type="linearmeasure"><x1>200</x1><y1>200</y1></annotation></ndpviewstate>
</annotations>""")
        self.assertEqual(self._text(dom, "ShapeCount"), "0")

    def test_shape_count_matches_actual_shape_elements(self):
        dom = self._convert("count.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>1</x><y>2</y></point></pointlist>
  </annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>3</x><y>4</y></point></pointlist>
  </annotation></ndpviewstate>
</annotations>""")
        shape_count = int(self._text(dom, "ShapeCount"))
        actual = len([e for e in dom.getElementsByTagName("*") if e.tagName.startswith("Shape_")])
        self.assertEqual(shape_count, actual)

    def test_shapes_numbered_sequentially(self):
        dom = self._convert("seq.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>1</x><y>2</y></point></pointlist>
  </annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>3</x><y>4</y></point></pointlist>
  </annotation></ndpviewstate>
</annotations>""")
        self.assertEqual(len(dom.getElementsByTagName("Shape_1")), 1)
        self.assertEqual(len(dom.getElementsByTagName("Shape_2")), 1)

    def test_shape_has_point_count_and_vertices(self):
        dom = self._convert("points.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist>
      <point><x>300000000</x><y>400000000</y></point>
      <point><x>350000000</x><y>450000000</y></point>
    </pointlist>
  </annotation></ndpviewstate>
</annotations>""")
        self.assertEqual(self._text(dom, "PointCount"), "2")
        self.assertEqual(self._text(dom, "X_1"), "300000")
        self.assertEqual(self._text(dom, "Y_1"), "400000")
        self.assertEqual(self._text(dom, "X_2"), "350000")
        self.assertEqual(self._text(dom, "Y_2"), "450000")

    # ── coordinate conversion ─────────────────────────────

    def test_coordinates_converted_from_nm_to_um(self):
        dom = self._convert("coords.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
</annotations>""")
        self.assertEqual(int(self._text(dom, "X_CalibrationPoint_1")), 100000)
        self.assertEqual(int(self._text(dom, "Y_CalibrationPoint_1")), 200000)
        self.assertEqual(int(self._text(dom, "X_CalibrationPoint_2")), 150000)
        self.assertEqual(int(self._text(dom, "Y_CalibrationPoint_2")), 250000)

    def test_coordinates_rounded_to_nearest_integer(self):
        dom = self._convert("round.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>499</x><y>1501</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000</x><y>250000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000</x><y>300000</y></annotation></ndpviewstate>
</annotations>""")
        self.assertEqual(self._text(dom, "X_CalibrationPoint_1"), "0")
        self.assertEqual(self._text(dom, "Y_CalibrationPoint_1"), "2")

    # ── error paths ───────────────────────────────────────

    def test_less_than_3_regions_still_converts_with_fewer_calibration_points(self):
        dom = self._convert("short.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
</annotations>""")
        self.assertEqual(self._text(dom, "X_CalibrationPoint_1"), "100000")
        self.assertEqual(self._text(dom, "Y_CalibrationPoint_1"), "200000")
        self.assertEqual(self._text(dom, "X_CalibrationPoint_2"), "150000")
        self.assertEqual(self._text(dom, "Y_CalibrationPoint_2"), "250000")
        self.assertEqual(self._text(dom, "ShapeCount"), "0")

    def test_missing_calibration_data_raises_value_error(self):
        in_path = self._write_input("missing.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><!-- no annotation and no pointlist --></ndpviewstate>
</annotations>""")
        out_path = str(Path(self.tmp) / "missing_LMD.xml")
        with self.assertRaises(ValueError):
            convert_ndpa_to_lmd_core(in_path, out_path)

    def test_malformed_shape_point_raises_value_error(self):
        in_path = self._write_input("malformed.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist>
      <point><x>300000000</x></point>
    </pointlist>
  </annotation></ndpviewstate>
</annotations>""")
        out_path = str(Path(self.tmp) / "malformed_LMD.xml")
        with self.assertRaises(ValueError):
            convert_ndpa_to_lmd_core(in_path, out_path)

    def test_invalid_xml_raises(self):
        in_path = self._write_input("bad.xml", "this is not xml <<<>>>")
        out_path = str(Path(self.tmp) / "bad_LMD.xml")
        with self.assertRaises(Exception):
            convert_ndpa_to_lmd_core(in_path, out_path)

    def test_nonexistent_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            convert_ndpa_to_lmd_core("/nonexistent/file.ndpa", "/nonexistent/out.xml")

    # ── using test_data files ─────────────────────────────

    def test_converts_real_valid_sample_from_test_data(self):
        test_data_dir = Path(__file__).parent / "test_data"
        input_file = str(test_data_dir / "valid_sample.ndpa")
        output_file = str(Path(self.tmp) / "valid_sample_LMD.xml")
        convert_ndpa_to_lmd_core(input_file, output_file)
        dom = minidom.parse(output_file)
        self.assertEqual(self._text(dom, "ShapeCount"), "2")
        self.assertEqual(self._text(dom, "X_CalibrationPoint_1"), "100000")
        self.assertEqual(self._text(dom, "Y_CalibrationPoint_1"), "200000")

    def test_converts_ruler_sample_from_test_data(self):
        test_data_dir = Path(__file__).parent / "test_data"
        input_file = str(test_data_dir / "ruler_sample.ndpa")
        output_file = str(Path(self.tmp) / "ruler_sample_LMD.xml")
        convert_ndpa_to_lmd_core(input_file, output_file)
        dom = minidom.parse(output_file)
        self.assertEqual(self._text(dom, "ShapeCount"), "2")
