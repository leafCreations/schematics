---
name: agent-self-evaluation
description: >-
  Mandatory end-of-turn review for every agent response in structure_scripts.
  Always run before handing off to the user — no exceptions. Includes skill and
  rule feedback loop. Implementation turns must update ≥1 skill and ≥1 rule. Pairs with agent-triage at task start. Enforced by
  .cursor/rules/agent-self-evaluation.mdc (alwaysApply).
---

# Agent Self-Evaluation

**Hard constraint:** every response to the user MUST end with §7 handoff block.  
Start tasks with [agent-triage](../agent-triage/SKILL.md). **Always** end with this skill.

Also enforced in `.cursor/rules/agent-self-evaluation.mdc` (`alwaysApply: true`).

## When to run

**Every turn.** Including:

- Implementation, fix, refactor, docs edit
- Read-only Q&A and explanations (Ask mode)
- Failed commit, blocked work, partial progress
- Single-line or one-file surgical changes

**There is no skip list.** If you are about to send a message to the user, run self-evaluation first.

## 1. Scope check

| Question | Pass if |
| -------- | ------- |
| Did the request ask for this change? | Every modified file ties to the task |
| Any drive-by refactors or doc sweeps? | None unless user asked |
| Any unrelated formatting across files? | Only touched paths formatted |

**Fail →** revert or split unrelated edits before handoff.

## 2. Process check (agent-triage)

```
- [ ] Classified request correctly (read-only / surgical / implementation)
- [ ] Used grep/targeted read before broad explore
- [ ] Opened only relevant rules/skills for the area
- [ ] Did not read main_window.py whole-file without grep first
- [ ] Did not run full pytest without justification
```

**Fail →** run missing step if cheap; capture gap in §6 skill & rule feedback.

## 3. Correctness check

| Area touched | Verify |
| ------------ | ------ |
| Kanban / card implementation | [docs/feature-areas.yaml](../../docs/feature-areas.yaml) updated; **`docs/`** reviewed per [docs-maintenance](../docs-maintenance/SKILL.md); **`## Acceptance Criteria`** marked `[x]` before **Review** (feature/bug); bug → **Corrective Action**; inquiry → **Response** only; **§6:** ≥1 skill + ≥1 rule updated |
| Structure YAML / editor save | Manifest vs `stage.yaml` split correct ([repo-map](../repo-map/SKILL.md)) |
| UI panel/dialog | [ui-change](../ui-change/SKILL.md) checklist |
| Registry/palette | `validate_palettes()` if behavior/palette changed; **templated families** use one token + materials, not raw catalog ids in `blocks:` ([repo-map](../repo-map/SKILL.md) § Templated block families) |
| Tests added/changed | No hard-coded catalog block counts ([targeted-testing](../targeted-testing/SKILL.md)) |
| Docs updated | Mandatory per [docs-maintenance](../docs-maintenance/SKILL.md) when code/behavior changed; handoff lists paths or `n/a` + why |

Read-only turns: mark N/A for rows that do not apply.

## 4. Verification check

| Done? | Evidence |
| ----- | -------- |
| Tests run | Name which files ran and result (pass/fail/not run + why) |
| Ruff clean on touched `.py` | Or pre-commit ruff hook would pass |
| Pre-commit path | If user will commit: hooks order known ([pre-commit-workflow](../pre-commit-workflow/SKILL.md)) |

**Never claim tests passed if they were not executed.** Read-only: `Tests: n/a (no code changes)`.

## 5. Churn review

Note anything that cost extra turns, tokens, or user corrections:

| Signal | Worth capturing? |
| ------ | ---------------- |
| Wrong file/path assumption | Yes — if likely to recur |
| Missing test mapping | Yes — add to targeted-testing or repo-map |
| Hook failure with non-obvious fix | Yes — pre-commit-workflow |
| UI wiring trap | Yes — ui-change or `.cursor/rules/ui-*.mdc` |
| User had to repeat a process expectation | Yes — update skill and/or rule |
| One-off typo or bad local edit | No |
| Task-specific business logic only | No — belongs in code/docs, not skills/rules |

**Implementation / fix / refactor turns** (any turn that changed application code, tests for behavior, or `docs/` / kanban / registry workflow):

- **Mandatory:** identify and apply **at least one improvement in a skill** and **at least one improvement in a rule** before handoff.
- Improvements may cover different aspects (skill = how-to/workflow; rule = constraint for matching paths) — do not duplicate the same bullet in both.
- If no obvious rule target exists, add a minimal `globs`-scoped reminder to the closest area `.mdc` (e.g. `ui-change` area → `ui-general.mdc` or the specific `ui-*.mdc` touched).

## 6. Skill & rule feedback loop (core)

**Every turn**, ask both:

1. *What **skill** improvement would make the next similar task faster or safer?*
2. *What **rule** improvement would prevent a repeat mistake on the paths we touched?*

**Implementation / fix / refactor turns:** you **must** edit **at least one skill file and at least one rule file** (`.cursor/rules/*.mdc`) in the same turn. Handoff `Skills updated:` and `Rules updated:` must each name a concrete change — not `none`.

**Read-only / Ask turns:** edits optional; handoff may use `none (read-only)` for either line.

If a learning applies → **edit in the same turn** before handoff. Do not only promise to update later.

Do **not** paste the same bullet into skill and rule — pair a workflow tip (skill) with a path-scoped constraint (rule).

### 6a. Skill vs rule — where to write

| Artifact | Use for |
| -------- | ------- |
| **Skill** (`.cursor/skills/*/SKILL.md`, `reference.md`) | Workflows, checklists, path→test maps, how-to, kanban lifecycle |
| **Rule** (`.cursor/rules/*.mdc`) | Mandatory constraints, `alwaysApply` behavior, `globs`-scoped reminders when editing matching paths |

### 6b. Pick the target

| Learning type | Skill | Rule (when constraint fits) |
| ------------- | ----- | --------------------------- |
| Wrong Minecraft version (1.x vs 26.x), bad web lookup | [project-context](../project-context/SKILL.md) | — |
| Tool choice, read budget, when to explore | [agent-triage](../agent-triage/SKILL.md) | [agent-self-evaluation.mdc](../../rules/agent-self-evaluation.mdc) if always-on |
| Kanban card types / sections | [kanban-markdown](../kanban-markdown/SKILL.md) | [kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc), [kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc) |
| Where code lives, save targets, layout | [repo-map](../repo-map/SKILL.md) | — |
| Which tests to run, catalog counts, Qt sandbox | [targeted-testing](../targeted-testing/SKILL.md) | [testing.mdc](../../rules/testing.mdc) if hook-level |
| Ruff / palette / pytest hook order | [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | — |
| Panel/dialog/grid wiring | [ui-change](../ui-change/SKILL.md) | [ui-dialogs.mdc](../../rules/ui-dialogs.mdc), [ui-panels.mdc](../../rules/ui-panels.mdc), etc. |
| Cross-cutting failure pattern | [reference.md](reference.md) § Common failure patterns | Owning area `.mdc` if editing that path should always trigger check |
| Self-eval not run / skipped | This skill | [agent-self-evaluation.mdc](../../rules/agent-self-evaluation.mdc) |

Prefer **`reference.md`** for examples, path→test rows, and failure-pattern tables.  
Prefer **`SKILL.md`** for procedures; prefer **`.mdc`** when the learning is a hard constraint on future edits in a file glob.

### 6c. What to add

Good additions (durable, generalizable):

- "When X fails, check Y first"
- Path → test row missing from pre-commit map
- Wrong mental model ("not `stage1/structure.yaml`, use `stage.yaml`")
- Sandbox/permission note for a test class
- Hook-specific fix order
- New kanban label type → scoped rule or row in existing kanban rule

Bad additions (skip):

- Restating code that changes every week
- Long prose or duplicate of an existing row
- Task-specific variable names with no reuse
- Entire conversation summaries
- Same bullet in both a skill and a rule

### 6d. How to edit

1. **Grep** the target skill or rule — do not duplicate an existing row or bullet.
2. **Minimal diff** — one table row, one bullet, or one short subsection.
3. **Concrete** — name files, tests, commands, or rule paths; avoid vague advice.
4. If a skill section grows past ~15 lines of accumulated tips, **consolidate** or move detail to `reference.md`.
5. Rules: keep `description` and `globs` accurate; use `alwaysApply: true` only for cross-cutting mandates.

### 6e. When to skip file edits

| Turn type | Skills | Rules |
| --------- | ------ | ----- |
| **Implementation / fix / refactor** | **Required** — ≥1 edit | **Required** — ≥1 edit |
| Read-only / Ask | Optional — `none (read-only)` | Optional — `none (read-only)` |
| User forbids skill/rule changes | `none (user requested)` | `none (user requested)` |
| Learning uncertain | Rare on implementation — prefer a small rule reminder over skipping | Same |

**Do not skip the handoff block or the §6 questions** — only skip file writes on read-only turns or explicit user opt-out.

## 7. Handoff format (required every turn)

**Last section of every response.** Compact; do not repeat the full diff.

```markdown
### Self-evaluation
- **Scope:** <on-target | read-only | note drift>
- **Tests:** <paths run + result | n/a + why>
- **Docs:** <paths updated | n/a + why>
- **Skills used:** <e.g. ui-change, targeted-testing | none>
- **Skills updated:** <skill name + one-line what added | none + why — not allowed on implementation turns>
- **Rules updated:** <rule path + one-line what added | none + why — not allowed on implementation turns>
- **Commit-ready:** <yes | needs pre-commit | n/a>
```

Read-only example:

```markdown
### Self-evaluation
- **Scope:** read-only — explained registry layout
- **Tests:** n/a (no code changes)
- **Docs:** n/a (read-only, no edits)
- **Skills used:** repo-map
- **Skills updated:** none (read-only)
- **Rules updated:** none (read-only)
- **Commit-ready:** n/a
```

## 8. Commit-specific add-on

If the user asked to commit or pre-commit failed:

```
- [ ] Staged files match described changes
- [ ] record-pytest-pass.sh run if pytest was manual and green
- [ ] No --no-verify unless user requested
- [ ] Commit message reflects why, not only what
- [ ] If pre-commit taught something new → pre-commit-workflow skill or testing rule updated (§6)
```

## 9. When to escalate to the user

Ask instead of guessing when:

- Task needs full suite but you only ran targeted tests and risk is unclear
- Manifest vs stage save behavior is ambiguous for the feature
- UI change needs manual visual check and UI was not launched
- Two valid architectures (user decision)
- Skill or rule update would change team workflow (new mandatory step) — propose first

Escalation does **not** exempt you from §7 handoff.

## Related skills

| Skill | Role |
| ----- | ---- |
| [agent-triage](../agent-triage/SKILL.md) | Task **start** routing; receives triage learnings |
| [repo-map](../repo-map/SKILL.md) | Layout sanity |
| [targeted-testing](../targeted-testing/SKILL.md) | Test discipline |
| [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | Hook order |
| [ui-change](../ui-change/SKILL.md) | UI checklist |
| [docs-maintenance](../docs-maintenance/SKILL.md) | Mandatory `docs/` sync after code changes |

Rubrics, examples, and update templates: [reference.md](reference.md).
