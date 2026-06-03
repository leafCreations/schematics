# Development Setup

Requires **Python 3.11+**.

On Ubuntu and other PEP 668 systems, use a virtual environment rather than installing into the system Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

For world generation, also install the optional Amulet stack:

```bash
pip install -e ".[dev,worldgen]"
```

For the desktop structure editor, install the `[ui]` extra and see [ui.md](ui.md).

```bash
pip install -e ".[dev,ui]"
python -m ui --structure residence --stage 1
```

PySide6 6.5+ needs a few X11 libraries that pip does not install. If startup fails with
`Could not load the Qt platform plugin "xcb"` or mentions `xcb-cursor0`, install:

```bash
sudo apt install libxcb-cursor0
```

Optional but recommended on multi-monitor X11 setups:

```bash
sudo apt install libxcb-xinerama0
```

On a Wayland session you can often bypass X11 entirely:

```bash
QT_QPA_PLATFORM=wayland python -m ui --structure residence --stage 1
```

The editor runs a preflight check on Linux and prints these instructions when the
libraries are missing. Full UI guide: [ui.md](ui.md).

See [worldgen.md](worldgen.md) and [../AMULET_INSTALL_NOTES.md](../AMULET_INSTALL_NOTES.md) if Amulet install fails.

## Git hooks

Install hooks (Ruff fix/format + re-stage on each commit):

```bash
pre-commit install
```

**Default commit:** runs Ruff only (~instant). Tests are not re-run on every commit.

**When you want tests before committing:**

```bash
pytest
# or
pre-commit run pytest --hook-stage manual
```

**Run everything (Ruff + pytest):**

```bash
pre-commit run --all-files --hook-stage manual
pre-commit run ruff-fix-format --all-files
```

Fix lint/format issues manually at any time:

```bash
scripts/ruff-fix
```

## Running checks

```bash
ruff check .
ruff format .
pytest
pre-commit run --all-files
```

## Dependencies

Runtime (via `pyproject.toml`):

* `Pillow`
* `PyYAML`
* `amulet-core` (world generation only; optional extra)

Dev (optional `[dev]` extra):

* `pytest`
* `ruff`
* `pre-commit`
