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

When any hook fails, a **`commit-issue`** kanban card may be written under `.devtool/features/` (label `commit-issue`) with hook output and failed test files. The hook prints `commit-issue card created: .devtool/features/commit-issue-<hook>-<timestamp>.md` after ruff/pytest/palette failure. Disable with `SKIP_COMMIT_ISSUE_CARD=1`. Cards are local (`.devtool/` is gitignored). If commit fails but no card appears, stage hook infra (`scripts/pre-commit-*.sh`, `scripts/on_pre_commit_failure.sh`, `scripts/create_commit_issue_card.py`) — pre-commit stashes unstaged hook changes (`precommit-stash-old-hooks` in pre-commit-workflow reference). Durable hook patterns: `.cursor/skills/pre-commit-workflow/reference.md` § Failure patterns.

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

## Cursor agent workflow

Agent routing and kanban process live outside application code:

- [AGENTS.md](../AGENTS.md) — entry point; card types (`agent`, `bug`, `inquiry`, `commit-issue`); **Feature Areas** / **Feature Area** → **Label Paths** + **Label Methods**
- [kanban-markdown/SKILL.md](../.cursor/skills/kanban-markdown/SKILL.md) — card lifecycle; registry maintenance
- `python scripts/resolve_feature_areas.py "<label>"` — paths; `--handlers` for registry entry-point symbols

* [AGENTS.md](../AGENTS.md) — entry index for Cursor agents
* [Consistency matrix](../.cursor/skills/agent-triage/reference.md#consistency-matrix) — governance artifact parity lookup
* [Drift alert examples](../.cursor/skills/agent-triage/reference.md#drift-alert-examples) — five named prefixes for parity warnings (matrix / audit anchors)
* **Surfacing:** governance-edit turns — Context load (self-eval §2b check 5), §6g, handoff `- **Drift alerts:**` — [agent-self-evaluation/SKILL.md](../.cursor/skills/agent-self-evaluation/SKILL.md) §6g; detection — [agent-triage/SKILL.md](../.cursor/skills/agent-triage/SKILL.md) § Governance drift detection
* `.cursor/rules/agent-consistency.mdc` — same-turn parity when editing governance skills, rules, or `AGENTS.md`
* Self-eval §6g — [agent-self-evaluation/SKILL.md](../.cursor/skills/agent-self-evaluation/SKILL.md) — end-of-turn consistency prompts when those paths change

### Periodic governance audit

Suggested **quarterly** (or after large agent/kanban epics): create a todo audit card and assign the agent to compare artifacts read-only:

```bash
python3 scripts/create_governance_audit_card.py
```

Full procedure: [kanban-markdown/SKILL.md](../.cursor/skills/kanban-markdown/SKILL.md) § Periodic AGENTS.md governance audit. Options: `--date YYYY-MM-DD`, `--force` to overwrite same-day card.

Checklist summary:

1. AGENTS.md Every turn ↔ agent-triage ↔ agent-routing.mdc
2. Card types ↔ kanban-*.mdc ↔ kanban-markdown
3. Failure-pattern Signatures ↔ reference tables ↔ [Consistency matrix](../.cursor/skills/agent-triage/reference.md#consistency-matrix)
4. `feature-areas.yaml` `handlers:` (malformed, cross-area duplicates) ↔ kanban **Label Methods** on open cards
5. Handoff format ↔ agent-self-evaluation §7
6. docs/development.md agent section ↔ AGENTS.md

Record drift on the audit card **## Audit findings**; spawn fix cards per bullet — do not fix silently during the audit turn.

### On-demand parity check

Ad-hoc drift detection between audits (uses phase 1 alert prefixes — paste output into Context load / handoff):

```bash
python3 scripts/check_governance_parity.py
```

Options: `--quiet` (exit code only). `--plain` omits `[severity]` prefixes. **`--no-spawn-cards`** skips kanban card creation. By default, each new drift issue spawns a **todo** card under `.devtool/features/` (epic `GovernanceDriftAlert`, priority from severity) with **## Alert**, **## Feature Areas**, **## Label Paths**, and **## Corrective Action** — duplicates skipped when the same alert already has an open card. Registry checks include optional `handlers:` symbols (malformed lines, duplicates across areas, kanban **Label Methods** missing from yaml).

## Dependencies

Runtime (via `pyproject.toml`):

* `Pillow`
* `PyYAML`
* `amulet-core` (world generation only; optional extra)

Dev (optional `[dev]` extra):

* `pytest`
* `ruff`
* `pre-commit`
