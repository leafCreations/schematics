---
name: agent-self-evaluation
description: >-
  Mandatory end-of-turn review for every agent response in structure_scripts.
  Always run before handing off to the user — no exceptions. Includes skill
  feedback loop. Pairs with agent-triage at task start. Enforced by
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

**Fail →** run missing step if cheap; capture gap in §6 skill feedback.

## 3. Correctness check

| Area touched | Verify |
| ------------ | ------ |
| Structure YAML / editor save | Manifest vs `stage.yaml` split correct ([repo-map](../repo-map/SKILL.md)) |
| UI panel/dialog | [ui-change](../ui-change/SKILL.md) checklist |
| Registry/palette | `validate_palettes()` if behavior/palette changed; **templated families** use one token + materials, not raw catalog ids in `blocks:` ([repo-map](../repo-map/SKILL.md) § Templated block families) |
| Tests added/changed | No hard-coded catalog block counts ([targeted-testing](../targeted-testing/SKILL.md)) |
| Docs updated | Only if user-facing or user asked; paths match manifest layout |

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
| UI wiring trap | Yes — ui-change |
| User had to repeat a process expectation | Yes — update skill or this rule |
| One-off typo or bad local edit | No |
| Task-specific business logic only | No — belongs in code/docs, not skills |

If **any** churn signal fired, §6 skill edit is **strongly preferred**. If **two or more**, §6 edit is **required** before handoff.

## 6. Skill feedback loop (core)

**Every turn:** ask *Would a one-line addition to a skill have prevented this churn or mistake?*

If yes → **edit the skill in the same turn** before handoff. Do not only promise to update later.

If no → handoff must still say `Skills updated: none` (not omit the line).

### 6a. Pick the target

| Learning type | Update |
| ------------- | ------ |
| Wrong Minecraft version (1.x vs 26.x), bad web lookup | [project-context/SKILL.md](../project-context/SKILL.md) or [reference.md](../project-context/reference.md) |
| Tool choice, read budget, when to explore | [agent-triage/SKILL.md](../agent-triage/SKILL.md) or [reference.md](../agent-triage/reference.md) |
| Where code lives, save targets, layout | [repo-map/SKILL.md](../repo-map/SKILL.md) or [reference.md](../repo-map/reference.md) |
| Which tests to run, catalog counts, Qt sandbox | [targeted-testing/SKILL.md](../targeted-testing/SKILL.md) or [reference.md](../targeted-testing/reference.md) |
| Ruff / palette / pytest hook order | [pre-commit-workflow/SKILL.md](../pre-commit-workflow/SKILL.md) |
| Panel/dialog/grid wiring | [ui-change/SKILL.md](../ui-change/SKILL.md) |
| Cross-cutting failure pattern | [reference.md](reference.md) § Common failure patterns |
| Self-eval not run / skipped | This skill + `.cursor/rules/agent-self-evaluation.mdc` |

Prefer **`reference.md`** for examples, path→test rows, and failure-pattern tables.  
Prefer **`SKILL.md`** for a single actionable rule an agent reads every time.

### 6b. What to add

Good additions (durable, generalizable):

- "When X fails, check Y first"
- Path → test row missing from pre-commit map
- Wrong mental model ("not `stage1/structure.yaml`, use `stage.yaml`")
- Sandbox/permission note for a test class
- Hook-specific fix order

Bad additions (skip):

- Restating code that changes every week
- Long prose or duplicate of an existing row
- Task-specific variable names with no reuse
- Entire conversation summaries

### 6c. How to edit

1. **Grep** the target skill — do not duplicate an existing row or bullet.
2. **Minimal diff** — one table row, one bullet, or one short subsection.
3. **Concrete** — name files, tests, or commands; avoid vague advice.
4. If a skill section grows past ~15 lines of accumulated tips, **consolidate** or move detail to `reference.md`.

### 6d. When to skip skill file edits

Only skip **editing skill files** when:

- User explicitly asked for no skill changes
- Learning is uncertain — handoff: `Skills updated: none (uncertain)`

**Do not skip the handoff block or the §6 question** — only skip writing to skill files.

## 7. Handoff format (required every turn)

**Last section of every response.** ≤6 lines. Do not repeat the full diff.

```markdown
### Self-evaluation
- **Scope:** <on-target | read-only | note drift>
- **Tests:** <paths run + result | n/a + why>
- **Skills used:** <e.g. ui-change, targeted-testing | none>
- **Skills updated:** <skill name + one-line what added | none>
- **Commit-ready:** <yes | needs pre-commit | n/a>
```

Read-only example:

```markdown
### Self-evaluation
- **Scope:** read-only — explained registry layout
- **Tests:** n/a (no code changes)
- **Skills used:** repo-map
- **Skills updated:** none
- **Commit-ready:** n/a
```

## 8. Commit-specific add-on

If the user asked to commit or pre-commit failed:

```
- [ ] Staged files match described changes
- [ ] record-pytest-pass.sh run if pytest was manual and green
- [ ] No --no-verify unless user requested
- [ ] Commit message reflects why, not only what
- [ ] If pre-commit taught something new → pre-commit-workflow skill updated (§6)
```

## 9. When to escalate to the user

Ask instead of guessing when:

- Task needs full suite but you only ran targeted tests and risk is unclear
- Manifest vs stage save behavior is ambiguous for the feature
- UI change needs manual visual check and UI was not launched
- Two valid architectures (user decision)
- Skill update would change team workflow (new mandatory step) — propose first

Escalation does **not** exempt you from §7 handoff.

## Related skills

| Skill | Role |
| ----- | ---- |
| [agent-triage](../agent-triage/SKILL.md) | Task **start** routing; receives triage learnings |
| [repo-map](../repo-map/SKILL.md) | Layout sanity |
| [targeted-testing](../targeted-testing/SKILL.md) | Test discipline |
| [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | Hook order |
| [ui-change](../ui-change/SKILL.md) | UI checklist |

Rubrics, examples, and update templates: [reference.md](reference.md).
