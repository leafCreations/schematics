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

See [worldgen.md](worldgen.md) and [../AMULET_INSTALL_NOTES.md](../AMULET_INSTALL_NOTES.md) if Amulet install fails.

## Git hooks

Install hooks (auto-fixes Ruff issues and re-stages files before each commit):

```bash
pre-commit install
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

The pre-commit hook runs Ruff (with `--fix`, re-staging changed files) and pytest before each commit.

## Dependencies

Runtime (via `pyproject.toml`):

* `Pillow`
* `PyYAML`
* `amulet-core` (world generation only; optional extra)

Dev (optional `[dev]` extra):

* `pytest`
* `ruff`
* `pre-commit`
