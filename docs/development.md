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
