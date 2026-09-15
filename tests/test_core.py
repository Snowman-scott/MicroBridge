from pathlib import Path
from xml.dom import minidom
from xml.dom.minidom import Text

import pytest

from MicroBridge.Core.core import convert_ndpa_to_lmd_core, derive_output_filename

TEST_DATA_DIR = Path(__file__).parent / "test_data" / "ndp"


def write_input(tmp_path: Path, name: str, xml: str) -> str:
    p = tmp_path / name
    p.write_text(xml, encoding="utf-8")
    return str(p)


def convert(tmp_path: Path, input_name: str, xml: str) -> minidom.Document:
    in_path = write_input(tmp_path, input_name, xml)
    out_path = tmp_path / f"{Path(input_name).stem}_LMD.xml"
    convert_ndpa_to_lmd_core(in_path, str(out_path))
    return minidom.parse(str(out_path))


def text(dom: minidom.Document, tag: str) -> str | None:
    els = dom.getElementsByTagName(tag)
    if not els:
        return None
    first_child = els[0].firstChild
    if not isinstance(first_child, Text):
        return None
    return first_child.data


# ── derive_output_filename ───────────────────────────────

def test_appends_lmd_xml_suffix():
    assert derive_output_filename("/data/sample.ndpa") == str(Path("/data/sample_LMD.xml"))


def test_handles_file_without_extension():
    assert derive_output_filename("/data/sample") == str(Path("/data/sample_LMD.xml"))


def test_keeps_different_directory():
    assert derive_output_filename("/some/other/path/foo.ndpa") == str(Path("/some/other/path/foo_LMD.xml"))


# ── happy path ───────────────────────────────────────────

def test_converts_valid_ndpa(tmp_path):
    dom = convert(tmp_path, "test.ndpa", """<?xml version="1.0"?>
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
    assert text(dom, "GlobalCoordinates") == "1"
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert text(dom, "Y_CalibrationPoint_1") == "200000"
    assert text(dom, "ShapeCount") == "1"


def test_output_xml_structure_has_all_expected_elements(tmp_path):
    dom = convert(tmp_path, "struct.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>300000000</x><y>400000000</y></point></pointlist>
  </annotation></ndpviewstate>
</annotations>""")
    assert len(dom.getElementsByTagName("ImageData")) == 1
    assert len(dom.getElementsByTagName("GlobalCoordinates")) == 1
    for i in range(1, 4):
        assert len(dom.getElementsByTagName(f"X_CalibrationPoint_{i}")) == 1
        assert len(dom.getElementsByTagName(f"Y_CalibrationPoint_{i}")) == 1
    assert len(dom.getElementsByTagName("ShapeCount")) == 1
    assert len(dom.getElementsByTagName("Shape_1")) == 1


def test_calibration_extracted_via_annotation_method(tmp_path):
    dom = convert(tmp_path, "cal_annot.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>50000000</x><y>75000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>125000000</x><y>175000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
</annotations>""")
    assert text(dom, "X_CalibrationPoint_1") == "50000"
    assert text(dom, "Y_CalibrationPoint_1") == "75000"
    assert text(dom, "X_CalibrationPoint_2") == "125000"
    assert text(dom, "Y_CalibrationPoint_2") == "175000"
    assert text(dom, "X_CalibrationPoint_3") == "200000"
    assert text(dom, "Y_CalibrationPoint_3") == "300000"


def test_calibration_via_pointlist_fallback_when_annotation_missing(tmp_path):
    dom = convert(tmp_path, "cal_pointlist.ndpa", """<?xml version="1.0"?>
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
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert text(dom, "Y_CalibrationPoint_1") == "200000"


def test_calibration_pointlist_fallback_when_annotation_has_no_xy(tmp_path):
    dom = convert(tmp_path, "cal_annot_no_xy.ndpa", """<?xml version="1.0"?>
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
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert text(dom, "Y_CalibrationPoint_1") == "200000"


# ── shape extraction ─────────────────────────────────────

def test_ruler_annotation_skipped(tmp_path):
    dom = convert(tmp_path, "ruler.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="linearmeasure"><x1>100</x1><y1>100</y1></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>300000000</x><y>400000000</y></point></pointlist>
  </annotation></ndpviewstate>
</annotations>""")
    assert text(dom, "ShapeCount") == "1"


def test_only_rulers_produces_zero_shapes(tmp_path):
    dom = convert(tmp_path, "ruler_only.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="linearmeasure"><x1>100</x1><y1>100</y1></annotation></ndpviewstate>
  <ndpviewstate><annotation type="linearmeasure"><x1>200</x1><y1>200</y1></annotation></ndpviewstate>
</annotations>""")
    assert text(dom, "ShapeCount") == "0"


def test_shape_count_matches_actual_shape_elements(tmp_path):
    dom = convert(tmp_path, "count.ndpa", """<?xml version="1.0"?>
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
    shape_count = int(text(dom, "ShapeCount") or 0)
    actual = len([e for e in dom.getElementsByTagName("*") if e.tagName.startswith("Shape_")])
    assert shape_count == actual


def test_shapes_numbered_sequentially(tmp_path):
    dom = convert(tmp_path, "seq.ndpa", """<?xml version="1.0"?>
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
    assert len(dom.getElementsByTagName("Shape_1")) == 1
    assert len(dom.getElementsByTagName("Shape_2")) == 1


def test_shape_has_point_count_and_vertices(tmp_path):
    dom = convert(tmp_path, "points.ndpa", """<?xml version="1.0"?>
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
    assert text(dom, "PointCount") == "2"
    assert text(dom, "X_1") == "300000"
    assert text(dom, "Y_1") == "400000"
    assert text(dom, "X_2") == "350000"
    assert text(dom, "Y_2") == "450000"


# ── coordinate conversion ────────────────────────────────

def test_coordinates_converted_from_nm_to_um(tmp_path):
    dom = convert(tmp_path, "coords.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
</annotations>""")
    assert int(text(dom, "X_CalibrationPoint_1") or 0) == 100000
    assert int(text(dom, "Y_CalibrationPoint_1") or 0) == 200000
    assert int(text(dom, "X_CalibrationPoint_2") or 0) == 150000
    assert int(text(dom, "Y_CalibrationPoint_2") or 0) == 250000


def test_coordinates_rounded_to_nearest_integer(tmp_path):
    dom = convert(tmp_path, "round.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>499</x><y>1501</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000</x><y>250000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000</x><y>300000</y></annotation></ndpviewstate>
</annotations>""")
    assert text(dom, "X_CalibrationPoint_1") == "0"
    assert text(dom, "Y_CalibrationPoint_1") == "2"


# ── error paths ──────────────────────────────────────────

def test_less_than_3_regions_still_converts_with_fewer_calibration_points(tmp_path):
    dom = convert(tmp_path, "short.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
</annotations>""")
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert text(dom, "Y_CalibrationPoint_1") == "200000"
    assert text(dom, "X_CalibrationPoint_2") == "150000"
    assert text(dom, "Y_CalibrationPoint_2") == "250000"
    assert text(dom, "ShapeCount") == "0"


def test_missing_calibration_data_raises_value_error(tmp_path):
    in_path = write_input(tmp_path, "missing.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><!-- no annotation and no pointlist --></ndpviewstate>
</annotations>""")
    out_path = str(tmp_path / "missing_LMD.xml")
    with pytest.raises(ValueError):
        convert_ndpa_to_lmd_core(in_path, out_path)


def test_malformed_shape_point_raises_value_error(tmp_path):
    in_path = write_input(tmp_path, "malformed.ndpa", """<?xml version="1.0"?>
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
    out_path = str(tmp_path / "malformed_LMD.xml")
    with pytest.raises(ValueError):
        convert_ndpa_to_lmd_core(in_path, out_path)


def test_invalid_xml_raises(tmp_path):
    in_path = write_input(tmp_path, "bad.xml", "this is not xml <<<>>>")
    out_path = str(tmp_path / "bad_LMD.xml")
    with pytest.raises(Exception):
        convert_ndpa_to_lmd_core(in_path, out_path)


def test_nonexistent_file_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        convert_ndpa_to_lmd_core("/nonexistent/file.ndpa", "/nonexistent/out.xml")


# ── using test_data files ────────────────────────────────

def test_converts_real_valid_sample_from_test_data(tmp_path):
    input_file = str(TEST_DATA_DIR / "valid_sample.ndpa")
    output_file = str(tmp_path / "valid_sample_LMD.xml")
    convert_ndpa_to_lmd_core(input_file, output_file)
    dom = minidom.parse(output_file)
    assert text(dom, "ShapeCount") == "2"
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert text(dom, "Y_CalibrationPoint_1") == "200000"


def test_converts_ruler_sample_from_test_data(tmp_path):
    input_file = str(TEST_DATA_DIR / "ruler_sample.ndpa")
    output_file = str(tmp_path / "ruler_sample_LMD.xml")
    convert_ndpa_to_lmd_core(input_file, output_file)
    dom = minidom.parse(output_file)
    assert text(dom, "ShapeCount") == "2"
