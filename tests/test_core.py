import re
from pathlib import Path
from xml.dom import minidom
from xml.dom.minidom import Text

import pytest

from MicroBridge.Core.core import (
    NoReferencePointError,
    convert_ndpa_to_lmd_core,
    derive_output_filename,
)

TEST_DATA_DIR = Path(__file__).parent / "test_data" / "ndp"


def write_input(tmp_path: Path, name: str, xml: str) -> str:
    p = tmp_path / name
    p.write_text(xml, encoding="utf-8")
    return str(p)


def convert(tmp_path: Path, input_name: str, xml: str) -> minidom.Document:
    dom, _ = convert_with_warnings(tmp_path, input_name, xml)
    return dom


def convert_with_warnings(
    tmp_path: Path, input_name: str, xml: str
) -> tuple[minidom.Document, list[str]]:
    in_path = write_input(tmp_path, input_name, xml)
    out_path = tmp_path / f"{Path(input_name).stem}_LMD.xml"
    warnings = convert_ndpa_to_lmd_core(in_path, str(out_path))
    return minidom.parse(str(out_path)), warnings


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


# ── named reference points (ref_N) ───────────────────────

def ref(num: int, x: int, y: int, shape: str = "circle") -> str:
    if shape == "circle":
        body = f"<x>{x}</x><y>{y}</y>"
    else:
        body = f"<pointlist><point><x>{x}</x><y>{y}</y></point></pointlist>"
    return (
        f'<ndpviewstate><title>ref_{num}</title>'
        f'<annotation type="{shape}">{body}</annotation></ndpviewstate>'
    )


def shape_region(title: str, x: int, y: int) -> str:
    return (
        f"<ndpviewstate><title>{title}</title>"
        f'<annotation type="freehand"><pointlist>'
        f"<point><x>{x}</x><y>{y}</y></point>"
        f"</pointlist></annotation></ndpviewstate>"
    )


def test_ref_points_at_end_of_file_are_found(tmp_path):
    dom, warnings = convert_with_warnings(tmp_path, "tail_refs.ndpa", f"""<?xml version="1.0"?>
<annotations>
  {shape_region("1", 300000000, 400000000)}
  {shape_region("2", 500000000, 600000000)}
  {ref(1, 100000000, 200000000)}
  {ref(2, 150000000, 250000000)}
  {ref(3, 200000000, 300000000)}
</annotations>""")
    assert warnings == []
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert text(dom, "Y_CalibrationPoint_1") == "200000"
    assert text(dom, "X_CalibrationPoint_3") == "200000"
    assert text(dom, "ShapeCount") == "2"


def test_ref_points_scattered_through_file_are_found(tmp_path):
    dom, warnings = convert_with_warnings(tmp_path, "scattered.ndpa", f"""<?xml version="1.0"?>
<annotations>
  {shape_region("1", 300000000, 400000000)}
  {ref(2, 150000000, 250000000)}
  {shape_region("2", 500000000, 600000000)}
  {ref(1, 100000000, 200000000)}
  {shape_region("3", 700000000, 800000000)}
  {ref(3, 200000000, 300000000)}
</annotations>""")
    assert warnings == []
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert text(dom, "X_CalibrationPoint_2") == "150000"
    assert text(dom, "X_CalibrationPoint_3") == "200000"
    assert text(dom, "ShapeCount") == "3"


def test_ref_numbers_win_over_document_order(tmp_path):
    """ref_3 appearing first must still land in CalibrationPoint_3."""
    dom = convert(tmp_path, "reversed.ndpa", f"""<?xml version="1.0"?>
<annotations>
  {ref(3, 200000000, 300000000)}
  {ref(2, 150000000, 250000000)}
  {ref(1, 100000000, 200000000)}
</annotations>""")
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert text(dom, "X_CalibrationPoint_2") == "150000"
    assert text(dom, "X_CalibrationPoint_3") == "200000"


def test_ref_regions_are_not_also_emitted_as_shapes(tmp_path):
    """A freehand ref_N has a pointlist, so it must be excluded by index."""
    dom, warnings = convert_with_warnings(tmp_path, "no_double.ndpa", f"""<?xml version="1.0"?>
<annotations>
  {ref(1, 100000000, 200000000, shape="freehand")}
  {ref(2, 150000000, 250000000, shape="freehand")}
  {ref(3, 200000000, 300000000, shape="freehand")}
  {shape_region("1", 300000000, 400000000)}
</annotations>""")
    assert text(dom, "ShapeCount") == "1"
    assert text(dom, "X_1") == "300000"
    assert len(warnings) == 3


@pytest.mark.parametrize("title", ["ref_1", "REF_1", "Ref_1", "ref 1", "ref-1", "ref1", " ref_1 "])
def test_ref_title_separator_and_case_variants_accepted(tmp_path, title):
    dom = convert(tmp_path, "variants.ndpa", f"""<?xml version="1.0"?>
<annotations>
  <ndpviewstate><title>{title}</title>
    <annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  {ref(2, 150000000, 250000000)}
  {ref(3, 200000000, 300000000)}
</annotations>""")
    assert text(dom, "X_CalibrationPoint_1") == "100000"


@pytest.mark.parametrize("title", ["reference_1", "ref_4", "ref_0", "refs_1", "ROI_1", "1"])
def test_non_ref_titles_do_not_count_as_named_refs(tmp_path, title):
    """Anything outside the convention leaves the file on the positional fallback."""
    dom, warnings = convert_with_warnings(tmp_path, "notref.ndpa", f"""<?xml version="1.0"?>
<annotations>
  <ndpviewstate><title>{title}</title>
    <annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><title>b</title>
    <annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><title>c</title>
    <annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
</annotations>""")
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert any("first three regions" in w for w in warnings)


# ── named but not a circle → accept and warn ─────────────

def test_named_ref_that_is_not_a_circle_is_accepted_with_warning(tmp_path):
    dom, warnings = convert_with_warnings(tmp_path, "notcircle.ndpa", f"""<?xml version="1.0"?>
<annotations>
  {ref(1, 100000000, 200000000, shape="freehand")}
  {ref(2, 150000000, 250000000)}
  {ref(3, 200000000, 300000000)}
</annotations>""")
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert text(dom, "Y_CalibrationPoint_1") == "200000"
    assert len(warnings) == 1
    assert "ref_1" in warnings[0]
    assert "circle" in warnings[0]


def test_all_three_refs_non_circle_warns_three_times(tmp_path):
    _, warnings = convert_with_warnings(tmp_path, "nocircles.ndpa", f"""<?xml version="1.0"?>
<annotations>
  {ref(1, 100000000, 200000000, shape="freehand")}
  {ref(2, 150000000, 250000000, shape="freehand")}
  {ref(3, 200000000, 300000000, shape="freehand")}
</annotations>""")
    assert len(warnings) == 3
    assert {"ref_1", "ref_2", "ref_3"} == {w.split()[0] for w in warnings}


def test_circle_ref_produces_no_warning(tmp_path):
    _, warnings = convert_with_warnings(tmp_path, "circles.ndpa", f"""<?xml version="1.0"?>
<annotations>
  {ref(1, 100000000, 200000000)}
  {ref(2, 150000000, 250000000)}
  {ref(3, 200000000, 300000000)}
</annotations>""")
    assert warnings == []


# ── no usable reference points → error ───────────────────

@pytest.mark.parametrize("present,missing", [((1, 2), "ref_3"), ((1, 3), "ref_2"), ((2, 3), "ref_1"), ((1,), "ref_2")])
def test_partial_named_refs_raise(tmp_path, present, missing):
    """Naming any ref_N commits the file to the convention — no silent fallback."""
    regions = "\n  ".join(ref(n, 100000000 * n, 200000000 * n) for n in present)
    in_path = write_input(tmp_path, "partial.ndpa", f"""<?xml version="1.0"?>
<annotations>
  {regions}
  {shape_region("1", 300000000, 400000000)}
</annotations>""")
    with pytest.raises(NoReferencePointError) as excinfo:
        convert_ndpa_to_lmd_core(in_path, str(tmp_path / "partial_LMD.xml"))
    assert missing in str(excinfo.value)


def test_duplicate_ref_number_raises(tmp_path):
    in_path = write_input(tmp_path, "dupe.ndpa", f"""<?xml version="1.0"?>
<annotations>
  {ref(1, 100000000, 200000000)}
  {ref(1, 110000000, 210000000)}
  {ref(2, 150000000, 250000000)}
  {ref(3, 200000000, 300000000)}
</annotations>""")
    with pytest.raises(NoReferencePointError) as excinfo:
        convert_ndpa_to_lmd_core(in_path, str(tmp_path / "dupe_LMD.xml"))
    assert "ref_1" in str(excinfo.value)


def test_named_ref_with_no_coordinates_raises(tmp_path):
    in_path = write_input(tmp_path, "emptyref.ndpa", f"""<?xml version="1.0"?>
<annotations>
  <ndpviewstate><title>ref_1</title></ndpviewstate>
  {ref(2, 150000000, 250000000)}
  {ref(3, 200000000, 300000000)}
</annotations>""")
    with pytest.raises(NoReferencePointError) as excinfo:
        convert_ndpa_to_lmd_core(in_path, str(tmp_path / "emptyref_LMD.xml"))
    assert "ref_1" in str(excinfo.value)


def test_file_with_no_regions_at_all_raises(tmp_path):
    in_path = write_input(tmp_path, "empty.ndpa", """<?xml version="1.0"?>
<annotations>
</annotations>""")
    with pytest.raises(NoReferencePointError):
        convert_ndpa_to_lmd_core(in_path, str(tmp_path / "empty_LMD.xml"))


def test_no_reference_point_error_is_a_value_error():
    """The CLI and GUI only catch ValueError, so the new error must stay inside it."""
    assert issubclass(NoReferencePointError, ValueError)


# ── legacy (pre-MicroBridge) files keep working ──────────

def test_legacy_unnamed_file_falls_back_to_first_three_regions(tmp_path):
    dom, warnings = convert_with_warnings(tmp_path, "legacy.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>300000000</x><y>400000000</y></point></pointlist>
  </annotation></ndpviewstate>
</annotations>""")
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert text(dom, "ShapeCount") == "1"
    assert len(warnings) == 1
    assert "ref_1" in warnings[0]


def test_legacy_reference_point_titles_still_use_the_fallback(tmp_path):
    """Reference_Point_N predates the convention and is not a ref_N match."""
    dom, warnings = convert_with_warnings(tmp_path, "oldnames.ndpa", """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><title>Reference_Point_1</title>
    <annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><title>Reference_Point_2</title>
    <annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><title>Reference_point_3</title>
    <annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
</annotations>""")
    assert text(dom, "X_CalibrationPoint_1") == "100000"
    assert warnings != []


# ── the real 1_PD sample, refs moved to the end ──────────

def test_pd_sample_has_refs_at_end_and_matches_expected_output(tmp_path):
    """The refs sit last in this file; output must equal the committed reference XML."""
    input_file = str(TEST_DATA_DIR / "1_PD43850x_Tg_Ab.ndpi.ndpa")
    output_file = str(tmp_path / "1_PD43850x_Tg_Ab.ndpi_LMD.xml")
    warnings = convert_ndpa_to_lmd_core(input_file, output_file)

    assert warnings == []
    expected = (TEST_DATA_DIR / "1_PD43850x_Tg_Ab.ndpi_LMD.xml").read_text(encoding="utf-8")
    assert Path(output_file).read_text(encoding="utf-8") == expected


def test_pd_sample_ndpviewstate_ids_are_sequential():
    source = (TEST_DATA_DIR / "1_PD43850x_Tg_Ab.ndpi.ndpa").read_text(encoding="utf-8")
    ids = [int(i) for i in re.findall(r'<ndpviewstate id="(\d+)">', source)]
    assert ids == list(range(1, len(ids) + 1))


def test_pd_sample_ref_titles_are_the_last_three_regions():
    source = (TEST_DATA_DIR / "1_PD43850x_Tg_Ab.ndpi.ndpa").read_text(encoding="utf-8")
    titles = re.findall(r"<title>([^<]*)</title>", source)
    assert titles[-3:] == ["ref_1", "ref_2", "ref_3"]
