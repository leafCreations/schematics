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

Install hooks (Ruff, palette validation, targeted pytest on each commit):

```bash
pre-commit install
```

**Default commit** runs:

1. **Ruff** — fix/format staged Python, re-stage
2. **`validate_palettes()`** — registry/palette integrity
3. **Targeted pytest** — `scripts/pre-commit-pytest.sh` maps staged paths to related tests (see the `case` branches in that script). Unmapped or core changes (e.g. `registries/loader.py`, `conftest.py`) run the **full** suite.

When any hook fails, a **`commit-issue`** kanban card may be written under `.devtool/features/` (label `commit-issue`) with hook output and failed test files. Disable with `SKIP_COMMIT_ISSUE_CARD=1`. Cards are local (`.devtool/` is gitignored). Durable hook patterns: `.cursor/skills/pre-commit-workflow/reference.md` § Failure patterns.

**Full test suite** (before a PR or after a large refactor):

```bash
pytest
# or via hooks on all files:
pre-commit run pytest --all-files
```

**Run all hooks without committing:**

```bash
pre-commit run --all-files
```

Fix lint/format issues manually at any time:

```bash
scripts/ruff-fix
```

**Commit without pytest** (Ruff and palette checks still run):

```bash
gcn -m "your message"              # shell alias (see ~/.bashrc)
scripts/gcn -m "your message"      # same, from repo scripts/
scripts/commit-no-pytest -m "..."  # long name
```

Same as `SKIP=pytest git commit …`. Run `pytest` yourself before pushing when you use this.

## Running checks

```bash
ruff check .
ruff format .
pytest                    # full suite
pre-commit run --all-files
```

While editing, run only the tests you care about, e.g. `pytest tests/test_ui_document.py -q`.

## Dependencies

Runtime (via `pyproject.toml`):

* `Pillow`
* `PyYAML`
* `amulet-core` (world generation only; optional extra)

Dev (optional `[dev]` extra):

* `pytest`
* `ruff`
* `pre-commit`
