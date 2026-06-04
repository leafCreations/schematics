from ui.reload import _reload_command, _reload_module_name


def test_reload_uses_module_launcher(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["/repo/ui/__main__.py", "--structure", "residence", "--stage", "1"],
    )
    executable, args = _reload_command()
    assert args == [executable, "-m", "ui", "--structure", "residence", "--stage", "1"]


def test_reload_module_main_window(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["/repo/ui/main_window.py", "--structure", "x", "--stage", "2"],
    )
    assert _reload_module_name() == "ui.main_window"
