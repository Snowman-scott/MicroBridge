import unittest
import tempfile
import shutil
import types
import unittest.mock
from pathlib import Path


class _MockCTkBase:
    def __init__(self, *args, **kwargs):
        pass

    def title(self, *args, **kwargs):
        pass

    def geometry(self, *args, **kwargs):
        pass

    def minsize(self, *args, **kwargs):
        pass

    def grid_columnconfigure(self, *args, **kwargs):
        pass

    def grid_rowconfigure(self, *args, **kwargs):
        pass

    def after(self, ms, cb, *args):
        cb(*args)

    def mainloop(self):
        pass


MOCK_CTK = types.ModuleType("customtkinter")

MOCK_CTK.CTk = _MockCTkBase

for _cls in [
    "CTkFrame", "CTkLabel", "CTkButton", "CTkTextbox",
    "CTkComboBox", "CTkFont", "CTkBaseClass",
]:
    setattr(MOCK_CTK, _cls, unittest.mock.MagicMock())


class MockStringVar:
    def __init__(self, value="", **kwargs):
        self._val = value
    def get(self): return self._val
    def set(self, v): self._val = v

MOCK_CTK.StringVar = MockStringVar
MOCK_CTK.set_appearance_mode = unittest.mock.MagicMock()
MOCK_CTK.set_default_color_theme = unittest.mock.MagicMock()
MOCK_CTK.END = "end"
MOCK_CTK.DISABLED = "disabled"
MOCK_CTK.NORMAL = "normal"

import sys
sys.modules["customtkinter"] = MOCK_CTK

_mock_fd = types.ModuleType("tkinter.filedialog")
_mock_fd.askopenfilenames = unittest.mock.MagicMock(return_value=[])
_mock_fd.askdirectory = unittest.mock.MagicMock(return_value="")
sys.modules["tkinter.filedialog"] = _mock_fd

from MicroBridge.GUI.gui import App


VALID_NDPA = """<?xml version="1.0"?>
<annotations>
  <ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
  <ndpviewstate><annotation type="freehand">
    <pointlist><point><x>300000000</x><y>400000000</y></point></pointlist>
  </annotation></ndpviewstate>
</annotations>"""


def make_app():
    app = App.__new__(App)
    app.input_files = []
    app.output_dir = None
    app._converting = False
    app.after = lambda ms, cb, *a: cb(*a)
    app.convert_btn = unittest.mock.MagicMock()
    app.log_text = unittest.mock.MagicMock()
    app.files_text = unittest.mock.MagicMock()
    app.files_label = unittest.mock.MagicMock()
    app.output_label = unittest.mock.MagicMock()
    app.log_text.tag_config = unittest.mock.MagicMock()
    return app


class TestGuiConvertWorker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, name: str, content: str = VALID_NDPA) -> str:
        p = Path(self.tmp) / name
        p.write_text(content, encoding="utf-8")
        return str(p)

    def test_all_valid_files_convert(self):
        app = make_app()
        app.input_files = [self._write("a.ndpa"), self._write("b.ndpa")]
        app._log = unittest.mock.MagicMock()
        app._convert_worker()
        self.assertFalse(app._converting)
        self.assertTrue((Path(self.tmp) / "a_LMD.xml").exists())
        self.assertTrue((Path(self.tmp) / "b_LMD.xml").exists())

    def test_wrong_extension_skipped(self):
        app = make_app()
        bad = Path(self.tmp) / "data.txt"
        bad.write_text("hello", encoding="utf-8")
        app.input_files = [str(bad)]
        app._log = unittest.mock.MagicMock()
        app._convert_worker()
        self.assertFalse((Path(self.tmp) / "data_LMD.xml").exists())

    def test_mix_valid_and_invalid_extensions(self):
        app = make_app()
        app.input_files = [
            self._write("good.ndpa"),
            self._write("data.txt", "hello"),
        ]
        app._log = unittest.mock.MagicMock()
        app._convert_worker()
        self.assertTrue((Path(self.tmp) / "good_LMD.xml").exists())
        self.assertFalse((Path(self.tmp) / "data_LMD.xml").exists())

    def test_output_dir_override(self):
        out_dir = Path(self.tmp) / "custom"
        out_dir.mkdir()
        app = make_app()
        app.output_dir = str(out_dir)
        app.input_files = [self._write("slide.ndpa")]
        app._log = unittest.mock.MagicMock()
        app._convert_worker()
        self.assertTrue((out_dir / "slide_LMD.xml").exists())
        self.assertFalse((Path(self.tmp) / "slide_LMD.xml").exists())

    def test_conversion_failure_caught(self):
        app = make_app()
        bad = self._write(
            "bad.ndpa",
            '<?xml version="1.0"?><annotations>'
            '<ndpviewstate><annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>'
            '<ndpviewstate><annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>'
            '<ndpviewstate><annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>'
            '<ndpviewstate><annotation type="freehand"><pointlist><point><x>100</x></point></pointlist></annotation></ndpviewstate>'
            "</annotations>",
        )
        app.input_files = [bad]
        app._log = unittest.mock.MagicMock()
        app._convert_worker()
        self.assertFalse((Path(self.tmp) / "bad_LMD.xml").exists())

    def test_empty_file_list_does_nothing(self):
        app = make_app()
        app.input_files = []
        app._log = unittest.mock.MagicMock()
        app._convert_worker()
        self.assertFalse(app._converting)

    def test_convert_finished_resets_button(self):
        app = make_app()
        app.input_files = [self._write("x.ndpa")]
        app._log = unittest.mock.MagicMock()
        app._convert_worker()
        self.assertFalse(app._converting)
        app.convert_btn.configure.assert_called_with(state="normal", text="Convert")


class TestGuiSelectFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.app = make_app()

    def test_select_files_updates_input_list(self):
        files = [str(Path(self.tmp) / "a.ndpa"), str(Path(self.tmp) / "b.ndpa")]
        with unittest.mock.patch(
            "tkinter.filedialog.askopenfilenames", return_value=files
        ):
            self.app._select_files()
        self.assertEqual(self.app.input_files, files)

    def test_select_files_cancel_keeps_list_unchanged(self):
        self.app.input_files = ["existing.ndpa"]
        with unittest.mock.patch(
            "tkinter.filedialog.askopenfilenames", return_value=[]
        ):
            self.app._select_files()
        self.assertEqual(self.app.input_files, ["existing.ndpa"])

    def test_select_folder_scans_for_ndpa(self):
        (Path(self.tmp) / "a.ndpa").touch()
        (Path(self.tmp) / "b.txt").touch()
        (Path(self.tmp) / "c.ndpa").touch()
        with unittest.mock.patch(
            "tkinter.filedialog.askdirectory", return_value=self.tmp
        ):
            self.app._select_folder()
        self.assertEqual(len(self.app.input_files), 2)
        self.assertTrue(all(f.endswith(".ndpa") for f in self.app.input_files))

    def test_select_folder_cancel_keeps_list(self):
        self.app.input_files = ["old.ndpa"]
        with unittest.mock.patch(
            "tkinter.filedialog.askdirectory", return_value=""
        ):
            self.app._select_folder()
        self.assertEqual(self.app.input_files, ["old.ndpa"])

    def test_select_output_sets_output_dir(self):
        with unittest.mock.patch(
            "tkinter.filedialog.askdirectory", return_value=str(self.tmp)
        ):
            self.app._select_output()
        self.assertEqual(self.app.output_dir, str(self.tmp))
