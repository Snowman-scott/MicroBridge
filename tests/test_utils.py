import unittest
from MicroBridge.utils import should_use_cli

class TestShouldUseCli(unittest.TestCase):
    def test_no_args_returns_false(self):
        self.assertFalse(should_use_cli([]))

    def test_dash_dash_gui_returns_false(self):
        self.assertFalse(should_use_cli(["--gui"]))

    def test_case_insensitive(self):
        self.assertFalse(should_use_cli(["--GUI"]))

    def test_other_args_still_returns_true(self):
        self.assertTrue(should_use_cli(["file.ndpa", "-o", "out/"]))

    def test_gui_flag_among_other_args(self):
        self.assertFalse(should_use_cli(["file.ndpa", "--gui"]))
