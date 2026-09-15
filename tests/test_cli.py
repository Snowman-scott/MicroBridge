from pathlib import Path

import pytest
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


@pytest.fixture
def runner():
    return CliRunner()


def _write(tmp_path: Path, name: str, content: str = VALID_NDPA) -> str:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return str(p)


# ── convert_files ────────────────────────────────────────

def test_all_files_succeed(tmp_path):
    f1 = _write(tmp_path, "a.ndpa")
    f2 = _write(tmp_path, "b.ndpa")
    successful, failures = convert_files([f1, f2], output=None)
    assert successful == 2
    assert failures == []


def test_wrong_extension_skipped(tmp_path):
    f1 = _write(tmp_path, "a.txt", "not ndpa")
    successful, failures = convert_files([f1], output=None)
    assert successful == 0
    assert len(failures) == 1
    assert "Expected a '.ndpa' file" in str(failures[0][1])


def test_conversion_failure_reported(tmp_path):
    f1 = _write(tmp_path, "bad.ndpa", MALFORMED_SHAPE_NDPA)
    successful, failures = convert_files([f1], output=None)
    assert successful == 0
    assert len(failures) == 1


def test_mix_of_valid_and_invalid(tmp_path):
    f1 = _write(tmp_path, "good.ndpa")
    f2 = _write(tmp_path, "bad.ndpa", MALFORMED_SHAPE_NDPA)
    successful, failures = convert_files([f1, f2], output=None)
    assert successful == 1
    assert len(failures) == 1


def test_empty_file_list():
    successful, failures = convert_files([], output=None)
    assert successful == 0
    assert failures == []


def test_output_directory_override(tmp_path):
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    f1 = _write(tmp_path, "a.ndpa")
    successful, failures = convert_files([f1], output=str(out_dir))
    assert successful == 1
    assert (out_dir / "a_LMD.xml").exists()


def test_output_directory_creates_file_with_lmd_suffix(tmp_path):
    f1 = _write(tmp_path, "data.ndpa")
    successful, failures = convert_files([f1], output=None)
    assert successful == 1
    assert (tmp_path / "data_LMD.xml").exists()


# ── find_ndpa_files ──────────────────────────────────────

def test_finds_ndpa_files(tmp_path):
    (tmp_path / "a.ndpa").touch()
    (tmp_path / "b.ndpa").touch()
    (tmp_path / "c.txt").touch()
    files = find_ndpa_files(str(tmp_path))
    assert len(files) == 2
    assert all(f.endswith(".ndpa") for f in files)


def test_ignores_non_ndpa(tmp_path):
    (tmp_path / "readme.txt").touch()
    (tmp_path / "data.csv").touch()
    files = find_ndpa_files(str(tmp_path))
    assert files == []


def test_empty_directory(tmp_path):
    files = find_ndpa_files(str(tmp_path))
    assert files == []


def test_nonexistent_directory_raises():
    with pytest.raises(FileNotFoundError):
        find_ndpa_files("/nonexistent/path")


# ── run command ──────────────────────────────────────────

def test_no_args_prints_help_and_exits_1(runner):
    result = runner.invoke(run, [])
    assert result.exit_code != 0
    assert "Usage" in result.output


def test_both_files_and_batch_errors(runner, tmp_path):
    f1 = _write(tmp_path, "a.ndpa")
    result = runner.invoke(run, [f1, "--batch", str(tmp_path)])
    assert result.exit_code != 0
    assert "cannot have files" in result.output


def test_single_file_converts_successfully(runner, tmp_path):
    f1 = _write(tmp_path, "sample.ndpa")
    result = runner.invoke(run, [f1])
    assert result.exit_code == 0
    assert (tmp_path / "sample_LMD.xml").exists()
    assert "Successfully" in result.output


def test_batch_directory_converts_all(runner, tmp_path):
    _write(tmp_path, "a.ndpa")
    _write(tmp_path, "b.ndpa")
    result = runner.invoke(run, ["--batch", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "a_LMD.xml").exists()
    assert (tmp_path / "b_LMD.xml").exists()


def test_batch_empty_directory_exits_0(runner, tmp_path):
    result = runner.invoke(run, ["--batch", str(tmp_path)])
    assert result.exit_code == 0


def test_output_flag_with_single_file(runner, tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    f1 = _write(tmp_path, "data.ndpa")
    result = runner.invoke(run, [f1, "--output", str(out_dir)])
    assert result.exit_code == 0
    assert (out_dir / "data_LMD.xml").exists()


def test_output_flag_with_batch(runner, tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _write(tmp_path, "a.ndpa")
    _write(tmp_path, "b.ndpa")
    result = runner.invoke(run, ["--batch", str(tmp_path), "--output", str(out_dir)])
    assert result.exit_code == 0
    assert (out_dir / "a_LMD.xml").exists()
    assert (out_dir / "b_LMD.xml").exists()


def test_mixed_valid_invalid_reports_failure(runner, tmp_path):
    _write(tmp_path, "good.ndpa")
    (tmp_path / "bad.ndpa").write_text(MALFORMED_SHAPE_NDPA, encoding="utf-8")
    result = runner.invoke(run, ["--batch", str(tmp_path)])
    assert result.exit_code != 0
    assert "failed" in result.output