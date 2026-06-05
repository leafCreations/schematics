# Test optimization reference (pytest)

## Quick wins checklist

1. `pytest --durations=20` — find outliers
2. `pytest --collect-only -q` — count tests per file; large files are consolidation targets
3. Grep for duplicate patterns: same `assert` blocks, identical fixture bodies, repeated `Path("assets")`
4. Check `conftest.py` for `autouse` fixtures
5. Check imports at module level that pull heavy deps for all tests in file

## Parametrize patterns

```python
@pytest.mark.parametrize("token,visible", [("A", True), (".", False)], ids=["block", "empty"])
def test_visibility(token, visible):
    assert is_visible(token) is visible
```

```python
@pytest.mark.parametrize(
    "cells,expected",
    [
        ([["."]], []),
        ([["A"]], [(0, 0)]),
    ],
)
def test_occupied(cells, expected):
    assert occupied_cell_positions(cells) == expected
```

## Fixture scope examples

```python
@pytest.fixture(scope="session")
def block_registry():
    from registries.loader import load_block_palettes
    return load_block_palettes()


@pytest.fixture
def mutable_grid(block_registry):
    return empty_cells(4, 4)  # fresh per test
```

## Markers

```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: expensive test")
    config.addinivalue_line("markers", "requires_assets: needs assets/minecraft")

# pytest.ini or pyproject.toml
# addopts = -m "not slow"   # only if user wants default fast runs
```

## Anti-patterns

| Anti-pattern | Fix |
| ------------ | --- |
| New test file per one-liner assert | Parametrize in existing module test file |
| `time.sleep` in tests | Mock time or poll with timeout |
| Loading 10MB YAML per test | `scope="session"` fixture or factory |
| `subprocess.run` full CLI | Test function layer directly |
| Identical `setup_method` in 10 classes | Module fixture |
| Testing private `_foo` when public API exists | Test public contract only |

## Measuring improvement

```bash
# Wall time
/usr/bin/time -f '%e' .venv/bin/pytest -q

# Per-test (verbose durations)
.venv/bin/pytest --durations=0 -q

# Single file before/after
/usr/bin/time .venv/bin/pytest tests/test_block_picker.py -q
```

## When to split (not consolidate)

- File exceeds ~400 lines **and** tests multiple unrelated modules
- Mixed unit + integration causing slow unit feedback
- Different fixture requirements (UI needs QApplication, helpers do not)

## Suggesting pytest-xdist

Only if user wants parallel runs and CI has CPU headroom:

```toml
# pyproject.toml optional — do not add without user approval
# dev = [..., "pytest-xdist"]
# addopts = "-n auto"
```

Downside: harder debugging, shared-state bugs if fixtures wrong.
