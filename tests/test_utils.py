from MicroBridge.utils import should_use_cli


def test_no_args_returns_false():
    assert should_use_cli([]) is False


def test_dash_dash_gui_returns_false():
    assert should_use_cli(["--gui"]) is False


def test_case_insensitive():
    assert should_use_cli(["--GUI"]) is False


def test_other_args_still_returns_true():
    assert should_use_cli(["file.ndpa", "-o", "out/"]) is True


def test_gui_flag_among_other_args():
    assert should_use_cli(["file.ndpa", "--gui"]) is False
