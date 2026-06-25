# Development Setup

Requires **Python 3.11+**.

On Ubuntu and other PEP 668 systems, use a virtual environment rather than installing into the system Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Virtualenv for agents:** use **`.venv` only** — never create `.tmp-venv` or other
throwaway venvs in the repo (Signature: `agent-no-tmp-venv`). If `.venv` is
missing, run the commands above or ask the user to set it up before running
pytest. Staging a venv tree breaks the ruff hook (Signature:
`precommit-ruff-staged-venv`).

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
- [kanban-markdown/SKILL.md](../.cursor/skills/kanban-markdown/SKILL.md) — card lifecycle; **prior lessons gate** before Decisions/CA; registry maintenance
- `python scripts/resolve_feature_areas.py "<label>"` — paths; `--handlers` for registry entry-point symbols; `--lessons` for curated `lesson_signatures` / `lesson_docs`
- `python3 scripts/resolve_prior_lessons.py --epic "<Epic>" "<Feature Area>" --paths …` — done/archived-card lessons + open commit-issue overlap + **Registry lesson pointers** when present
- `python3 scripts/build_lessons_index.py` — regenerate `docs/lessons-index.yaml` from Card Done captures; `--check` for stale index; `--dry-run` to stdout; `--sync-registry` proposes `lesson_*` keys in `docs/feature-areas.yaml` (dry-run; add `--write` to apply)

### Lessons reference index

Committed registry of promoted lessons grouped by feature area (paths + Signatures only — not full card prose).

| Field | Meaning |
| ----- | ------- |
| `version` | Schema version (`1`) |
| `generated_at` | ISO-8601 UTC timestamp from last generator run |
| `areas.<label>.signatures` | Promotion Signatures grep'd from done/archived cards |
| `areas.<label>.done_cards` | Relative paths to cards with `## Lessons captured` |
| `areas.<label>.artifacts` | Governance links (skills, rules, docs) from lesson bullets |

Refresh after **Card Done** lessons capture or before a quarterly governance audit:

```bash
python3 scripts/build_lessons_index.py
python3 scripts/build_lessons_index.py --check   # exit 1 when stale
```

**Agent read order (kanban pre-implementation):** skim the card's area block in `docs/lessons-index.yaml`, then [agent-triage/reference.md](../.cursor/skills/agent-triage/reference.md) § **Lessons by area**, then `resolve_prior_lessons.py` — open full done cards only when still ambiguous ([kanban-prior-lessons-gate.mdc](../.cursor/rules/kanban-prior-lessons-gate.mdc)).

When `.devtool/features/` is absent (CI clone without kanban), the generator skips writing; tests use `tmp_path` fixtures.

Epic `LessonsReferenceIndex` (li0–li3) — index build (this section), structured `artifacts:` on cards, registry pointers, triage routing.

### Feature area lesson pointers (li2)

Optional per-area keys in `docs/feature-areas.yaml`:

| Key | Meaning |
| --- | ------- |
| `lesson_signatures` | Curated promotion Signatures (≤8) — grep targets without opening done cards |
| `lesson_docs` | Developer doc paths (≤5) — highlights from lesson captures |

**Manual curation first:** seed and trim lists when closing cards; keep highlights small, not full index dumps.

**Automation suggests only:** `python3 scripts/build_lessons_index.py --sync-registry` prints proposed `lesson_*` diffs from `docs/lessons-index.yaml` (dry-run). Add `--write` to apply when you accept the proposal.

```bash
python3 scripts/resolve_feature_areas.py --lessons "Render Preview"
python3 scripts/resolve_feature_areas.py --agents-parity "Render Preview"
python3 scripts/resolve_prior_lessons.py "Render Preview" --paths helpers/orbit_face_textures.py
```

**`--agents-parity` (gs3):** prints `agents_skill`, `agents_rules`, `lesson_routing_row`, and whether the `lesson_routing_row` anchor appears in [agent-triage/reference.md](../.cursor/skills/agent-triage/reference.md) § **Lessons by area** (`lessons_by_area_row: found|missing|n/a`). Use during kanban pre-implementation review alongside `--lessons`. Single area label per invocation is typical.

```bash
pytest tests/test_resolve_feature_areas.py -q -k agents_parity
```

Dual **Feature Area** labels on a card union pointers from each resolved area.

### Governance area schema (gs0)

Optional per-area keys in `docs/feature-areas.yaml` for **mechanical** agent routing and parity checks — so prior-lessons gates and `check_governance_parity.py` do not rely on parsing AGENTS.md markdown tables.

| Key | Type | Purpose |
| --- | ---- | ------- |
| `agents_skill` | string | Primary skill stem (e.g. `ui-change`) — gate step loads `.cursor/skills/{stem}/SKILL.md` |
| `agents_rules` | list | Rule stems under `.cursor/rules/` with optional `#signature` (e.g. `ui-panels.mdc`, `testing.mdc#orbit-animated-texture-strip`) |
| `lesson_routing_row` | string \| null | Anchor label in [agent-triage/reference.md](../.cursor/skills/agent-triage/reference.md) § **Lessons by area** first column; `null` when `lessons-index.yaml` area block is enough |

**Relationship to lesson pointers and index:**

| Artifact | Role |
| -------- | ---- |
| `lesson_signatures` / `lesson_docs` (li2) | Curated grep/doc highlights per area — manual curation; `--lessons` on `resolve_feature_areas.py` |
| `docs/lessons-index.yaml` | Committed index of promoted Signatures, done cards, artifacts — built by `build_lessons_index.py` |
| `lesson_routing_row` | Links an area to a row in triage § **Lessons by area** for pre-implementation read order |
| `agents_skill` / `agents_rules` | Links an area to load-when-touching skills and scoped rules (`check_area_schema_parity` in `check_governance_parity.py` — gs2) |

All governance keys are **optional** and **backward compatible** — areas without them behave as today until gs1 seeds high-traffic areas.

**Out of scope (gs0–gs3):** editing or generating AGENTS.md **Area → skills & rules** table rows from yaml. That table stays narrative until a follow-up epic after mechanical parity lands.

**gs3 (complete):** `--agents-parity` on `resolve_feature_areas.py`; pytest `agents_parity` tests; pre-commit maps `feature-areas.yaml` / parity script changes to schema tests.

**gs1 seed areas (complete):** Render Preview, Agent Workflow, Properties Panel, Feature Area Registry, Palette Registry — `agents_skill`, `agents_rules`, `lesson_routing_row` in `docs/feature-areas.yaml`.

Epic `GovernanceAreaSchema` (gs0–gs3) — **complete**. Schema spec, five seeded areas, `check_area_schema_parity`, pytest + `--agents-parity`. **Follow-up epic:** AGENTS **Area → skills & rules** table sync or codegen from yaml.

### Lessons captured `artifacts:` schema

Optional **machine-readable tail** on each `## Lessons captured` lesson bullet. When present, `build_lessons_index.py` and `resolve_prior_lessons.py` prefer `artifacts:` over free-form **Governance** link heuristics.

**Per-lesson template:**

```markdown
- **Symptom:** animated furnace front tiles multiple openings in orbit preview.
- **Fix:** load frame 0 via `load_block_texture_image`; golden tests use same helper.
  - artifacts: skill:project-context, rule:testing.mdc#orbit-animated-texture-strip, doc:render-types.md, sig:orbit-animated-texture-strip, test:tests/test_block_texture_load.py
```

| Prefix | Value | Indexed as |
| ------ | ----- | ---------- |
| `skill:` | skill folder name (e.g. `project-context`) or full `.cursor/skills/…/SKILL.md` | skill path under `.cursor/skills/` |
| `rule:` | `filename.mdc` or `filename.mdc#signature` anchor | `.cursor/rules/filename.mdc` (anchor for humans) |
| `doc:` | doc basename or `docs/…` path (`.md`, `.yaml`, `.yml`) | path under `docs/` |
| `sig:` | promotion Signature slug | `areas.<label>.signatures` (not an artifact path) |
| `test:` | pytest file path | `tests/…` path in `areas.<label>.artifacts` |

One `artifacts:` sub-bullet per lesson (comma-separated entries). Cards without `artifacts:` still work — parsers fall back to **Governance** markdown links.

**`doc:` notes:** Markdown basenames may omit `.md` (`doc:render-types` → `docs/render-types.md`). Registry YAML under `docs/` **must** include the extension (`doc:lessons-index.yaml`, `doc:feature-areas.yaml`) — extensionless registry stems such as `doc:lessons-index` are skipped (Signature: `artifacts-doc-yaml-normalize`). Use `rule:` for `.mdc` files, not `doc:`.

**Overlap with `LessonsCoverageMetric` lc2:** lc2 scores **C2 promotion quality** on done cards (heuristic). This schema defines **authoring** for new captures; lc2 can treat structured `artifacts:` as higher-confidence C2 evidence in a later card.

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
