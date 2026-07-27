import unittest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner

from MicroBridge.CLI.cli import convert_files, find_ndpa_files, run

VALID_NDPA = """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>300000000</x><y>400000000</y></point></pointlist>
  </annotation></ndpviewstate>
</annotations>"""


MALFORMED_SHAPE_NDPA = """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist>
      <point><x>300000000</x></point>
    </pointlist>
  </annotation></ndpviewstate>
</annotations>"""


class TestConvertFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, name: str, content: str = VALID_NDPA) -> str:
        p = Path(self.tmp) / name
        p.write_text(content, encoding="utf-8")
        return str(p)

    def test_all_files_succeed(self):
        f1 = self._write("a.ndpa")
        f2 = self._write("b.ndpa")
        successful, failures = convert_files([f1, f2], output=None)
        self.assertEqual(successful, 2)
        self.assertEqual(failures, [])

    def test_wrong_extension_skipped(self):
        f1 = self._write("a.txt", "not ndpa")
        successful, failures = convert_files([f1], output=None)
        self.assertEqual(successful, 0)
        self.assertEqual(len(failures), 1)
        self.assertIn("Expected a '.ndpa' file", str(failures[0][1]))

    def test_conversion_failure_reported(self):
        f1 = self._write("bad.ndpa", MALFORMED_SHAPE_NDPA)
        successful, failures = convert_files([f1], output=None)
        self.assertEqual(successful, 0)
        self.assertEqual(len(failures), 1)

    def test_mix_of_valid_and_invalid(self):
        f1 = self._write("good.ndpa")
        f2 = self._write("bad.ndpa", MALFORMED_SHAPE_NDPA)
        successful, failures = convert_files([f1, f2], output=None)
        self.assertEqual(successful, 1)
        self.assertEqual(len(failures), 1)

    def test_empty_file_list(self):
        successful, failures = convert_files([], output=None)
        self.assertEqual(successful, 0)
        self.assertEqual(failures, [])

    def test_output_directory_override(self):
        out_dir = Path(self.tmp) / "output"
        out_dir.mkdir()
        f1 = self._write("a.ndpa")
        successful, failures = convert_files([f1], output=str(out_dir))
        self.assertEqual(successful, 1)
        self.assertTrue((out_dir / "a_LMD.xml").exists())

    def test_output_directory_creates_file_with_lmd_suffix(self):
        f1 = self._write("data.ndpa")
        successful, failures = convert_files([f1], output=None)
        self.assertEqual(successful, 1)
        self.assertTrue((Path(self.tmp) / "data_LMD.xml").exists())


class TestFindNdpaFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_finds_ndpa_files(self):
        (Path(self.tmp) / "a.ndpa").touch()
        (Path(self.tmp) / "b.ndpa").touch()
        (Path(self.tmp) / "c.txt").touch()
        files = find_ndpa_files(self.tmp)
        self.assertEqual(len(files), 2)
        self.assertTrue(all(f.endswith(".ndpa") for f in files))

    def test_ignores_non_ndpa(self):
        (Path(self.tmp) / "readme.txt").touch()
        (Path(self.tmp) / "data.csv").touch()
        files = find_ndpa_files(self.tmp)
        self.assertEqual(files, [])

    def test_empty_directory(self):
        files = find_ndpa_files(self.tmp)
        self.assertEqual(files, [])

    def test_nonexistent_directory_raises(self):
        with self.assertRaises(FileNotFoundError):
            find_ndpa_files("/nonexistent/path")


class TestRunCommand(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.runner = CliRunner()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, name: str, content: str = VALID_NDPA) -> str:
        p = Path(self.tmp) / name
        p.write_text(content, encoding="utf-8")
        return str(p)

    def test_no_args_prints_help_and_exits_1(self):
        result = self.runner.invoke(run, [])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Usage", result.output)

    def test_both_files_and_batch_errors(self):
        f1 = self._write("a.ndpa")
        result = self.runner.invoke(run, [f1, "--batch", self.tmp])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("cannot have files", result.output)

    def test_single_file_converts_successfully(self):
        f1 = self._write("sample.ndpa")
        result = self.runner.invoke(run, [f1])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue((Path(self.tmp) / "sample_LMD.xml").exists())
        self.assertIn("Successfully", result.output)

    def test_batch_directory_converts_all(self):
        self._write("a.ndpa")
        self._write("b.ndpa")
        result = self.runner.invoke(run, ["--batch", self.tmp])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue((Path(self.tmp) / "a_LMD.xml").exists())
        self.assertTrue((Path(self.tmp) / "b_LMD.xml").exists())

    def test_batch_empty_directory_exits_0(self):
        result = self.runner.invoke(run, ["--batch", self.tmp])
        self.assertEqual(result.exit_code, 0)

    def test_output_flag_with_single_file(self):
        out_dir = Path(self.tmp) / "out"
        out_dir.mkdir()
        f1 = self._write("data.ndpa")
        result = self.runner.invoke(run, [f1, "--output", str(out_dir)])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue((out_dir / "data_LMD.xml").exists())

    def test_output_flag_with_batch(self):
        out_dir = Path(self.tmp) / "out"
        out_dir.mkdir()
        self._write("a.ndpa")
        self._write("b.ndpa")
        result = self.runner.invoke(run, ["--batch", self.tmp, "--output", str(out_dir)])
        self.assertEqual(result.exit_code, 0)
        self.assertTrue((out_dir / "a_LMD.xml").exists())
        self.assertTrue((out_dir / "b_LMD.xml").exists())

    def test_mixed_valid_invalid_reports_failure(self):
        self._write("good.ndpa")
        (Path(self.tmp) / "bad.ndpa").write_text(MALFORMED_SHAPE_NDPA, encoding="utf-8")
        result = self.runner.invoke(run, ["--batch", self.tmp])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("failed", result.output)
