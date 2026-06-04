"""Restart the editor process (development reload)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _cli_args() -> list[str]:
    """Flags after the launcher (e.g. ``--structure``, ``--stage``)."""
    return list(sys.argv[1:])


def _reload_module_name() -> str:
    """Match how the editor was started (``python -m ui`` or ``python -m ui.main_window``)."""
    script = Path(sys.argv[0]).resolve()

    if script.name == "main_window.py" and script.parent.name == "ui":
        return "ui.main_window"

    return "ui"


def _reload_command() -> tuple[str, list[str]]:
    executable = sys.executable
    module = _reload_module_name()
    args = [executable, "-m", module, *_cli_args()]
    return executable, args


def _reload_environ() -> dict[str, str]:
    env = dict(os.environ)
    root = str(_project_root())
    existing = env.get("PYTHONPATH", "")

    if root not in existing.split(os.pathsep):
        env["PYTHONPATH"] = f"{root}{os.pathsep}{existing}" if existing else root

    return env


def reload_editor_process() -> None:
    """Replace the running process with a fresh ``python -m ui`` (or ``ui.main_window``)."""
    os.chdir(_project_root())
    executable, args = _reload_command()
    env = _reload_environ()

    if sys.platform == "win32":
        os.spawnve(os.P_WAIT, executable, args, env)
        raise SystemExit(0)

    os.execve(executable, args, env)
