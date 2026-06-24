# Agent Self-Evaluation — Reference

## Loop (start → work → improve → handoff)

```text
START → agent-triage (classify, pick tools, pick skills)
WORK  → minimal edits + targeted tests
END   → agent-self-evaluation
          ├─ checks (scope, process, correctness, verification)
          ├─ churn review
          ├─ update skill(s) if durable learning  ← required when applicable
          └─ compact handoff to user
```

The feedback loop is the **main deliverable** of self-evaluation. A checklist-only pass without skill updates wastes the next session's tokens.

## Update decision matrix

| Situation | Update skill? | Target |
| --------- | ------------- | ------ |
| User corrected wrong save target (manifest vs stage) | Yes | repo-map |
| Agent used 1.x Minecraft info from web search | Yes | project-context |
| Ran full pytest for one helper change | Yes | targeted-testing or agent-triage §4 |
| Pre-commit palette error: missing `top` texture exception | Yes | pre-commit-workflow |
| Discovered `test_foo.py` maps to changed path but missing from skill | Yes | targeted-testing/reference.md |
| Fixed typo in one string | No | — |
| New feature with no reusable pattern yet | No | — |
| Qt test segfault without `all` permissions | Yes | targeted-testing |
| Repeated grep for same symbol across tasks | Yes | repo-map reference (Where is X?) |

## Example skill updates

### Good — one table row (targeted-testing/reference.md)

```markdown
| `helpers/worldgen_site.py` | `tests/test_worldgen_site.py` |
```

### Good — one bullet (pre-commit-workflow/SKILL.md)

```markdown
- **Palette `top` missing:** if behavior has no `render.textures.top`, validate skips top check — do not add fake `top` keys.
```

### Good — failure pattern row (this reference)

```markdown
| Bed display name wrong color | materials.py uses `minecraft:{color}_bed` catalog id, not token alias |
```

### Bad — too vague

```markdown
- Be careful with tests
- Remember to read the code before editing
```

### Bad — duplicates existing guidance

Adding "use grep before reading main_window.py" when agent-triage §2 already says it.

## Example handoffs

### With skill update

```markdown
### Self-evaluation
- **Scope:** on-target — `helpers/materials.py` + test only
- **Tests:** `tests/test_materials.py` — 6 passed
- **Docs:** n/a (no user-facing workflow change)
- **Skills used:** targeted-testing
- **Skills updated:** targeted-testing/reference — added `helpers/log_materials.py` → test map row
- **Commit-ready:** yes (run pre-commit)
```

### No update needed

```markdown
### Self-evaluation
- **Scope:** on-target — single doc typo
- **Tests:** skipped (docs-only)
- **Docs:** `docs/ui.md` (typo fix)
- **Skills used:** repo-map
- **Skills updated:** none
- **Commit-ready:** yes
```

### Churn captured

```markdown
### Self-evaluation
- **Scope:** on-target but 12 files touched for palette count fix
- **Tests:** `tests/test_palette_panel.py` — passed (after unnecessary full suite)
- **Skills used:** agent-triage (late)
- **Skills updated:** agent-triage/reference — row: hard-coded terrain counts → use tests/palette_helpers.py
- **Commit-ready:** needs pre-commit
```

## Process ↔ skill map

| Triage step | Self-eval question | Skill to update if gap found |
| ----------- | ------------------ | ---------------------------- |
| §1 Classify | Did mode match actual work? | agent-triage |
| §2 Discovery | Too many reads/explores? | agent-triage |
| §3 Area rules | Skipped ui-change or worldgen rule? | ui-change or `.cursor/rules/` |
| §4 Testing | Claimed pass without run? | targeted-testing |
| §5 Pre-commit | Hook order followed on failure? | pre-commit-workflow |
| §6 Scope | Unrelated edits? | agent-triage |
| §8 Checklist | All boxes honestly ticked? Docs pass when code changed? | agent-self-evaluation, docs-maintenance |

## Common failure patterns in this repo

| Pattern | Prevention | Skill |
| ------- | ---------- | ----- |
| `stage1/structure.yaml` in docs/code | Use manifest + `stage.yaml` | repo-map |
| `assert count == 32` in palette tests | `tests/palette_helpers.py` | targeted-testing |
| Full pytest after `helpers/foo.py` tweak | pre-commit map first | targeted-testing |
| Dialog OK without `_persist_dialog_changes` | ui-change checklist | ui-change |
| `--no-verify` on hook failure | Fix hooks in order | pre-commit-workflow |
| Reading all of `main_window.py` | Grep first | agent-triage |
| Web search “minecraft 1.21” for repo task | project-context + docs/project-info.md | project-context |
| Added new blocks to palette as `minecraft:*` ids | One semantic token + `enumerate_token_materials`; mirror FENCE/SLAB wiring | repo-map |
| Worldgen tests: `template/` not found | Use `resolve_worldgen_template_dir()` → `worldgen_templates/v26_1_2/` | repo-map, project-context |
| Worldgen tests: Amulet `4903` interface missing | Template is 26.2 but Amulet only supports 26.1.x — default worldgen to `DEFAULT_WORLGEN_VERSION` | project-context |
| Commit failed pytest after “tests passed” earlier | Run `scripts/pre-commit-pytest.sh` on staged files before commit; re-run same scope after fixes | targeted-testing §5–§6, pre-commit-workflow |
| Shipped feature without `docs/` sync | Run [docs-maintenance](../docs-maintenance/SKILL.md) before Review / commit-ready | docs-maintenance |
| Self-eval skipped / missing handoff block | Violates `.cursor/rules/agent-self-evaluation.mdc` — required every turn | agent-self-evaluation |

Add rows here **and** to the owning skill when a new pattern appears twice.

## Read-only / Ask mode

Self-evaluation is **still required**. Use `Scope: read-only`, `Tests: n/a`, `Docs: n/a (read-only)`, `Commit-ready: n/a`. Skill edits only when the user asks or churn revealed a durable gap worth proposing.

## Maintenance

- **Consolidate** quarterly: merge duplicate rows across skills
- **Prune** tips that no longer match the codebase (stale paths, removed modules)
- Keep each `SKILL.md` under ~130 lines; overflow goes to `reference.md`
