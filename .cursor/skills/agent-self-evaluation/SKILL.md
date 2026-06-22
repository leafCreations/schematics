---
name: agent-self-evaluation
description: >-
  End-of-task self-review for structure_scripts agent work. Use before handing
  off to the user, after completing a feature or fix, when wrapping a commit,
  or when asked to reduce churn, reflect on token use, or verify the task is
  done. Updates relevant skills with durable learnings. Pairs with agent-triage
  at task start.
---

# Agent Self-Evaluation

Exit review **and skill feedback loop** before you tell the user the task is complete. Goal: **proficiency and churn reduction** — not only for this session, but for the next agent on the same task type.

Start tasks with [agent-triage](../agent-triage/SKILL.md). End with this skill.

## When to run

- Implementation or fix is **code-complete**
- Before saying "done", "ready to commit", or summarizing PR work
- After a failed commit loop (verify root cause fixed, not symptoms)
- **Skip** for pure Q&A in Ask mode with no edits

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
| Registry/palette | `validate_palettes()` if behavior/palette changed |
| Tests added/changed | No hard-coded catalog block counts ([targeted-testing](../targeted-testing/SKILL.md)) |
| Docs updated | Only if user-facing or user asked; paths match manifest layout |

## 4. Verification check

| Done? | Evidence |
| ----- | -------- |
| Tests run | Name which files ran and result (pass/fail/not run + why) |
| Ruff clean on touched `.py` | Or pre-commit ruff hook would pass |
| Pre-commit path | If user will commit: hooks order known ([pre-commit-workflow](../pre-commit-workflow/SKILL.md)) |

**Never claim tests passed if they were not executed.**

## 5. Churn review

Note anything that cost extra turns, tokens, or user corrections:

| Signal | Worth capturing? |
| ------ | ---------------- |
| Wrong file/path assumption | Yes — if likely to recur |
| Missing test mapping | Yes — add to targeted-testing or repo-map |
| Hook failure with non-obvious fix | Yes — pre-commit-workflow |
| UI wiring trap | Yes — ui-change |
| One-off typo or bad local edit | No |
| Task-specific business logic only | No — belongs in code/docs, not skills |

If **two or more** churn signals fired, §6 is **required** (not optional).

## 6. Skill feedback loop (core)

**After every non-trivial task**, ask: *Would a one-line addition to a skill have prevented this churn?*

If yes → **edit the skill in the same turn** before handoff. Do not only promise to update later.

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
| Meta: self-eval process itself | This skill |

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

### 6d. When to skip skill edits

- Ask/read-only with no churn
- Surgical fix with zero surprises and skills already covered it
- User explicitly asked for no skill changes
- Learning is uncertain — note in handoff under **Skills updated: none (uncertain)** instead of guessing

## 7. Handoff format

Use at the end of **implementation** responses (omit for trivial one-line answers):

```markdown
### Self-evaluation
- **Scope:** <on-target | note drift>
- **Tests:** <paths run + result, or why skipped>
- **Skills used:** <e.g. ui-change, targeted-testing — or none>
- **Skills updated:** <skill name + one-line what added | none>
- **Commit-ready:** <yes / needs pre-commit / docs-only>
```

Keep **6 lines max**. Do not repeat the full diff.

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

## Related skills

| Skill | Role |
| ----- | ---- |
| [agent-triage](../agent-triage/SKILL.md) | Task **start** routing; receives triage learnings |
| [repo-map](../repo-map/SKILL.md) | Layout sanity |
| [targeted-testing](../targeted-testing/SKILL.md) | Test discipline |
| [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | Hook order |
| [ui-change](../ui-change/SKILL.md) | UI checklist |

Rubrics, examples, and update templates: [reference.md](reference.md).
