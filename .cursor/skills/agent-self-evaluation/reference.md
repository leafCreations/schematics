# Agent Self-Evaluation — Reference

## Loop (start → work → improve → handoff)

```text
START → agent-triage (classify, pick tools, pick skills/rules)
WORK  → minimal edits + targeted tests
END   → agent-self-evaluation/SKILL.md
          ├─ ### Files used (load order)
          ├─ context load audit (4 checks incl. AGENTS.md)
          ├─ checks (scope, process, correctness, verification)
          ├─ churn review
          ├─ update skill(s) and/or rule(s) if durable learning  ← required when applicable
          └─ ### Self-evaluation handoff
```

The feedback loop is the **main deliverable** of self-evaluation. **Implementation turns** must leave **both** a skill and a rule smarter; checklist-only handoffs waste the next session's tokens.

## Skill vs rule

| Write to | When |
| -------- | ---- |
| **Skill** | Procedure, workflow, path→test map, kanban lifecycle, "how to" |
| **Rule** (`.cursor/rules/*.mdc`) | Mandatory constraint, `globs` reminder for a path class, `alwaysApply` behavior |

One learning per artifact — skill (workflow) + rule (constraint); do not duplicate the same bullet in both.

**Implementation turns:** both columns below must be **Yes** with an edit in the same turn.

## Update decision matrix

| Situation | Update? | Target |
| --------- | ------- | ------ |
| User corrected wrong save target (manifest vs stage) | Skill | repo-map |
| Agent used 1.x Minecraft info from web search | Skill | project-context |
| Ran full pytest for one helper change | Skill | targeted-testing or agent-triage §4 |
| Pre-commit palette error: missing `top` texture exception | Skill | pre-commit-workflow |
| Discovered `test_foo.py` maps to changed path but missing from skill | Skill | targeted-testing/reference.md |
| Fixed typo in one string | No | — |
| New kanban card label type (bug, inquiry, …) | Rule (+ skill) | `kanban-*.mdc` + kanban-markdown |
| Dialog OK without `_persist_dialog_changes` repeated | Rule | ui-dialogs.mdc |
| Qt test segfault without `all` permissions | Skill | targeted-testing |
| Repeated grep for same symbol across tasks | Skill | repo-map reference (Where is X?) |
| Self-eval handoff missing `Rules updated:` | Rule | agent-self-evaluation.mdc |

## Example skill updates

### Good — one table row (targeted-testing/reference.md)

```markdown
| `helpers/worldgen_site.py` | `tests/test_worldgen_site.py` |
```

### Good — one bullet (pre-commit-workflow/SKILL.md)

```markdown
- **Palette `top` missing:** if behavior has no `render.textures.top`, validate skips top check — do not add fake `top` keys.
```

## Example rule updates

### Good — one bullet (ui-dialogs.mdc)

```markdown
- After dialog OK on layer delete: call `_persist_dialog_changes`, not only `_mark_layer_dirty`.
```

### Good — new scoped rule (kanban-inquiry-cards.mdc)

Short rule file with `globs: .devtool/features/**/*.md` when a new kanban label type needs always-on section split.

### Bad — duplicate skill content in rule

Copying the full kanban lifecycle into a rule when kanban-markdown/SKILL.md already has it.

## Example handoffs

### Implementation handoff (both required)

```markdown
### Files used
1. `AGENTS.md` — routing entry
2. `.cursor/skills/ui-change/SKILL.md` — checklist
3. `ui/document.py` (edit) — dirty-flag fix
4. `tests/test_ui_document.py` — verify

### Self-evaluation
- **Scope:** on-target — preview dirty-flag fix
- **Context load:** ok — triage then targeted edit; AGENTS.md current
- **Tests:** `tests/test_ui_document.py` — 3 passed
- **Docs:** `docs/ui.md` — undo section
- **Skills used:** ui-change, targeted-testing
- **Skills updated:** targeted-testing/reference — `ui/document.py` → `tests/test_ui_document.py` row
- **Rules updated:** testing.mdc — reminder to run test_ui_document after `ui/document.py` edits
- **Commit-ready:** yes
```

### With rule update

```markdown
### Self-evaluation
- **Scope:** on-target — kanban inquiry workflow docs
- **Tests:** n/a (skills/rules only)
- **Docs:** n/a
- **Skills used:** kanban-markdown, agent-self-evaluation
- **Skills updated:** kanban-markdown — § Inquiry cards
- **Rules updated:** kanban-inquiry-cards.mdc — new scoped rule
- **Commit-ready:** yes
```

### No update needed

```markdown
### Self-evaluation
- **Scope:** read-only — single doc typo explanation
- **Tests:** n/a
- **Docs:** n/a (read-only)
- **Skills used:** repo-map
- **Skills updated:** none (read-only)
- **Rules updated:** none (read-only)
- **Commit-ready:** n/a
```

### Churn captured

```markdown
### Self-evaluation
- **Scope:** on-target but 12 files touched for palette count fix
- **Tests:** `tests/test_palette_panel.py` — passed (after unnecessary full suite)
- **Skills used:** agent-triage (late)
- **Skills updated:** agent-triage/reference — row: signature `palette-hardcoded-count` → tests/palette_helpers.py
- **Rules updated:** none (skill reference was sufficient)
- **Commit-ready:** needs pre-commit
```

## Process ↔ skill & rule map

| Triage step | Self-eval question | Skill to update if gap found | Rule to update if gap found |
| ----------- | ------------------ | ---------------------------- | --------------------------- |
| §1 Classify | Did mode match actual work? | agent-triage | — |
| §2 Discovery | Too many reads/explores? Files used listed? | agent-triage | agent-self-evaluation.mdc if handoff skipped |
| §3 Area rules | Skipped ui-change or worldgen rule? | ui-change | `.cursor/rules/ui-*.mdc`, worldgen.mdc |
| §4 Testing | Claimed pass without run? | targeted-testing | testing.mdc |
| §5 Pre-commit | Hook order followed on failure? | pre-commit-workflow | — |
| §6 Scope | Unrelated edits? | agent-triage | — |
| §6g Governance | Edited agent-consistency `globs`? | agent-self-evaluation §6g; [agent-triage/reference.md](../agent-triage/reference.md) § Consistency matrix | agent-consistency.mdc |
| §8 Checklist | Docs pass when code changed? | docs-maintenance | — |
| Kanban label type | Wrong section split on card? | kanban-markdown | kanban-bug-cards.mdc, kanban-inquiry-cards.mdc |

## Common failure patterns in this repo

Canonical cross-cutting table. Row schema: [SKILL.md](SKILL.md) §6f. Pre-commit hook patterns: [pre-commit-workflow/reference.md](../pre-commit-workflow/reference.md) § Failure patterns. Retrieval at task start: [agent-triage/SKILL.md](../agent-triage/SKILL.md) §1b.

| Signature | Trigger snippet | Fix pattern | Skill | Rule |
| --------- | --------------- | ----------- | ----- | ---- |
| `yaml-stage1-structure-yaml` | `stage1/structure.yaml` | Use manifest + `stage.yaml` | repo-map | — |
| `palette-hardcoded-count` | `assert count == 32` | Use `tests/palette_helpers.py` | targeted-testing | — |
| `ui-dialog-no-persist` | dialog OK without `_persist_dialog_changes` | ui-change checklist on accept | ui-change | ui-dialogs.mdc |
| `self-eval-skipped` | missing `### Self-evaluation` | Required every turn — §7 handoff | agent-self-evaluation | agent-self-evaluation.mdc |
| `self-eval-missing-rules-updated` | handoff missing `Rules updated:` | Handoff template §7 | agent-self-evaluation | agent-self-evaluation.mdc |
| `kanban-roadmap-queue` | `docs/roadmap.md` as task queue | Use [AGENTS.md](../../AGENTS.md) + agent-routing.mdc | agent-triage | agent-routing.mdc |
| `handoff-missing-files-context` | missing `### Files used` or **Context load** | §7 two-section end | agent-self-evaluation | agent-self-evaluation.mdc |
| `agents-md-stale` | workflow change without AGENTS.md update | §2b check 4 — update routing guide | agent-triage | agent-routing.mdc |
| `agent-skill-edit-no-agents-read` | edit under `.cursor/skills/agent-*/` or `kanban-*/` | Read AGENTS.md § Maintaining same turn | agent-self-evaluation | agent-agents-md-maintenance.mdc |
| `agent-no-tmp-venv` | `python3 -m venv .tmp-venv` or agent-created `.tmp-venv` for pytest | Use `.venv`: `pip install -e ".[dev]"` then `.venv/bin/pytest`; ask user to create `.venv` if missing — never stage throwaway venvs | targeted-testing | testing.mdc |
| `implementation-handoff-none-updates` | `Skills updated: none` or `Rules updated: none` on implementation | §6 requires both on implementation turns | agent-self-evaluation | agent-self-evaluation.mdc |
| `docs-not-synced-on-ship` | feature shipped without `docs/` sync | docs-maintenance before Review | docs-maintenance | — |
| `ruff-e501-line-length` | `E501 Line too long` on commit | Wrap strings; split lines ≤ 100 chars | pre-commit-workflow | agent-routing.mdc |
| `orbit-stair-mask-transparency` | orbit 3D holes / transparent treads / missing bottom; flat color on stone stairs | Solid tiles in `orbit_face_textures` (`PLANKS:*` or `minecraft:*`); no alpha discard; corner-probe `±Y`; see `docs/render-types.md` lessons | ui-change | kanban-bug-cards.mdc |
| `artifacts-doc-yaml-normalize` | `lessons-index.yaml.md` in index; `doc:lessons-index` skipped | `_normalize_doc_ref` keeps `.yaml`/`.yml`; Card Done uses explicit `doc:…yaml` for registry paths | targeted-testing | testing.mdc |

**Signature** = lowercase kebab-case grep key (optional area prefix). Rules cite **Signature** + this row — do not duplicate **Fix pattern** prose in `.mdc` files.

Add a row here when a pattern appears twice; link owning skill/rule by name only (workflow detail stays in those artifacts).

## Read-only / Ask mode

Self-evaluation is **still required**. Use `Scope: read-only`, `Tests: n/a`, `Docs: n/a (read-only)`, `Commit-ready: n/a`, `Skills updated: none (read-only)`, `Rules updated: none (read-only)`. Edit skills/rules only when the user asks or churn revealed a durable gap.

## Maintenance

- **Consolidate** quarterly: merge duplicate rows across skills and rules
- **Prune** tips that no longer match the codebase (stale paths, removed modules)
- Keep each `SKILL.md` under ~130 lines; overflow goes to `reference.md`
- Keep rules short; link to skills for long workflows
