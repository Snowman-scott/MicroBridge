from pathlib import Path
from xml.dom import minidom

import pytest
from click.testing import CliRunner

from MicroBridge.CLI.cli import run

from .helpers import element_text

VALID_NDPA = """<?xml version="1.0" encoding="utf-8"?>
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
    <title>ROI_1</title>
    <annotation type="freehand">
      <pointlist>
        <point><x>300000000</x><y>400000000</y></point>
        <point><x>350000000</x><y>450000000</y></point>
      </pointlist>
    </annotation>
  </ndpviewstate>
  <ndpviewstate id="5">
    <title>ROI_2</title>
    <annotation type="freehand">
      <pointlist>
        <point><x>500000000</x><y>600000000</y></point>
        <point><x>550000000</x><y>650000000</y></point>
        <point><x>525000000</x><y>625000000</y></point>
      </pointlist>
    </annotation>
  </ndpviewstate>
</annotations>
"""


@pytest.fixture
def runner():
    return CliRunner()


def _write_ndpa(tmp_path: Path, name: str) -> str:
    p = tmp_path / name
    p.write_text(VALID_NDPA, encoding="utf-8")
    return str(p)


def _parse_xml(path: Path) -> minidom.Document:
    return minidom.parse(str(path))


def test_single_file_via_cli_produces_valid_lmd_xml(runner, tmp_path):
    _write_ndpa(tmp_path, "slide1.ndpa")
    result = runner.invoke(run, [str(tmp_path / "slide1.ndpa")])
    assert result.exit_code == 0

    out = tmp_path / "slide1_LMD.xml"
    assert out.exists()
    dom = _parse_xml(out)

    assert element_text(dom, "GlobalCoordinates") == "1"
    assert element_text(dom, "X_CalibrationPoint_1") == "100000"
    assert element_text(dom, "ShapeCount") == "2"
    assert len(dom.getElementsByTagName("Shape_1")) == 1
    assert len(dom.getElementsByTagName("Shape_2")) == 1


def test_batch_converts_multiple_files(runner, tmp_path):
    _write_ndpa(tmp_path, "a.ndpa")
    _write_ndpa(tmp_path, "b.ndpa")
    result = runner.invoke(run, ["--batch", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "a_LMD.xml").exists()
    assert (tmp_path / "b_LMD.xml").exists()


def test_output_flag_routes_files_to_custom_directory(runner, tmp_path):
    out_dir = tmp_path / "custom_out"
    out_dir.mkdir()
    _write_ndpa(tmp_path, "data.ndpa")
    result = runner.invoke(run, ["--batch", str(tmp_path), "--output", str(out_dir)])
    assert result.exit_code == 0
    assert (out_dir / "data_LMD.xml").exists()
    assert not (tmp_path / "data_LMD.xml").exists()


def test_output_xml_uses_realistic_coordinates(runner, tmp_path):
    _write_ndpa(tmp_path, "realistic.ndpa")
    runner.invoke(run, [str(tmp_path / "realistic.ndpa")])
    dom = _parse_xml(tmp_path / "realistic_LMD.xml")

    for i in range(1, 4):
        x = int(element_text(dom, f"X_CalibrationPoint_{i}"))
        y = int(element_text(dom, f"Y_CalibrationPoint_{i}"))
        assert x > 0
        assert y > 0

    shape_count = int(element_text(dom, "ShapeCount"))
    assert shape_count == 2
    for s in range(1, shape_count + 1):
        shape_el = dom.getElementsByTagName(f"Shape_{s}")[0]
        point_count = int(element_text(shape_el, "PointCount"))
        assert point_count > 0


def test_failure_exit_code_on_malformed_file(runner, tmp_path):
    bad = tmp_path / "bad.ndpa"
    bad.write_text(
        '<?xml version="1.0"?><annotations>'
        '<ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>'
        '<ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>'
        '<ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>'
        '<ndpviewstate><annotation type="freehand"><pointlist><point><x>100</x></point></pointlist></annotation></ndpviewstate>'
        "</annotations>",
        encoding="utf-8",
    )
    result = runner.invoke(run, [str(bad)])
    assert result.exit_code != 0
