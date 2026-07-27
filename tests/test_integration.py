import unittest
import tempfile
import shutil
from pathlib import Path
from xml.dom import minidom
from click.testing import CliRunner

from MicroBridge.CLI.cli import run

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


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.runner = CliRunner()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_ndpa(self, name: str) -> str:
        p = Path(self.tmp) / name
        p.write_text(VALID_NDPA, encoding="utf-8")
        return str(p)

    def _parse_xml(self, path: Path) -> minidom.Document:
        return minidom.parse(str(path))

    def test_single_file_via_cli_produces_valid_lmd_xml(self):
        self._write_ndpa("slide1.ndpa")
        result = self.runner.invoke(run, [str(Path(self.tmp) / "slide1.ndpa")])
        self.assertEqual(result.exit_code, 0)

        out = Path(self.tmp) / "slide1_LMD.xml"
        self.assertTrue(out.exists())
        dom = self._parse_xml(out)

        self.assertEqual(
            dom.getElementsByTagName("GlobalCoordinates")[0].firstChild.data, "1"
        )
        self.assertEqual(
            dom.getElementsByTagName("X_CalibrationPoint_1")[0].firstChild.data,
            "100000",
        )
        self.assertEqual(
            dom.getElementsByTagName("ShapeCount")[0].firstChild.data, "2"
        )
        self.assertEqual(len(dom.getElementsByTagName("Shape_1")), 1)
        self.assertEqual(len(dom.getElementsByTagName("Shape_2")), 1)

    def test_batch_converts_multiple_files(self):
        self._write_ndpa("a.ndpa")
        self._write_ndpa("b.ndpa")
        result = self.runner.invoke(run, ["--batch", self.tmp])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue((Path(self.tmp) / "a_LMD.xml").exists())
        self.assertTrue((Path(self.tmp) / "b_LMD.xml").exists())

    def test_output_flag_routes_files_to_custom_directory(self):
        out_dir = Path(self.tmp) / "custom_out"
        out_dir.mkdir()
        self._write_ndpa("data.ndpa")
        result = self.runner.invoke(
            run, ["--batch", self.tmp, "--output", str(out_dir)]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertTrue((out_dir / "data_LMD.xml").exists())
        self.assertFalse((Path(self.tmp) / "data_LMD.xml").exists())

    def test_output_xml_uses_realistic_coordinates(self):
        self._write_ndpa("realistic.ndpa")
        self.runner.invoke(run, [str(Path(self.tmp) / "realistic.ndpa")])
        dom = self._parse_xml(Path(self.tmp) / "realistic_LMD.xml")

        for i in range(1, 4):
            x = int(
                dom.getElementsByTagName(f"X_CalibrationPoint_{i}")[
                    0
                ].firstChild.data
            )
            y = int(
                dom.getElementsByTagName(f"Y_CalibrationPoint_{i}")[
                    0
                ].firstChild.data
            )
            self.assertGreater(x, 0)
            self.assertGreater(y, 0)

        shape_count = int(
            dom.getElementsByTagName("ShapeCount")[0].firstChild.data
        )
        self.assertEqual(shape_count, 2)
        for s in range(1, shape_count + 1):
            shape_el = dom.getElementsByTagName(f"Shape_{s}")[0]
            point_count = int(
                shape_el.getElementsByTagName("PointCount")[0].firstChild.data
            )
            self.assertGreater(point_count, 0)

    def test_failure_exit_code_on_malformed_file(self):
        bad = Path(self.tmp) / "bad.ndpa"
        bad.write_text(
            '<?xml version="1.0"?><annotations>'
            '<ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>'
            '<ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>'
            '<ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>'
            '<ndpviewstate><annotation type="freehand"><pointlist><point><x>100</x></point></pointlist></annotation></ndpviewstate>'
            "</annotations>",
            encoding="utf-8",
        )
        result = self.runner.invoke(run, [str(bad)])
        self.assertNotEqual(result.exit_code, 0)
