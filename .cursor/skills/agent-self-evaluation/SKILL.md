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

**Track context load during the turn** — maintain a mental (or scratch) **ordered list** of every path read, edited, grepped-as-primary-source, or skill/rule loaded for decisions. You will output it in §7 **Files used**.

**Fail →** run missing step if cheap; capture gap in §6 skill & rule feedback.

## 2b. Context load audit (feeds §7)

Before handoff, score the turn against these checks:

| # | Check | Pass if |
| - | ----- | ------- |
| 1 | **Correct files loaded** | Every path read/edited was needed for the task; skills/rules match the area ([AGENTS.md](../../AGENTS.md) area table or triage §1) |
| 2 | **No excess load** | No whole-file reads that grep would replace; no explore/Task for a single needle; stayed within triage read budget (≤3 full reads before grep/search) unless justified |
| 3 | **Proper order** | **Classify before deep read** — [AGENTS.md](../../AGENTS.md) or [agent-triage](../agent-triage/SKILL.md) → area skill/rule → grep → targeted reads → edits → tests |
| 4 | **[AGENTS.md](../../AGENTS.md) not stale** | Routing guide still matches what you used: card types, area→skill table, turn lifecycle, handoff format. If this turn added a workflow (new label, skill, gate, script), **update AGENTS.md** in the same turn or flag **stale** in handoff |
| 5 | **Governance drift surfaced** (governance glob edits only) | After §6g matrix compare: parity fixed in the **same turn**, **or** Context load / handoff lists drift lines (`[severity]` optional — default `warn`) from [agent-triage/reference.md](../agent-triage/reference.md) § Drift alert examples, **or** `KNOWN_DRIFT: <artifact pair> — <reason>[; expires: …]` when user approved temporary drift. **N/A** when no governance paths edited |

**Fail any check →** note in **Context load** line (include drift alert prefix lines when check 5 fails); fix AGENTS.md or add a skill/rule row in §6 when durable.

## 3. Correctness check

| Area touched | Verify |
| ------------ | ------ |
| Kanban / card implementation | **Prompt verb gate** ([kanban-card-gates.mdc](../../rules/kanban-card-gates.mdc) §2); prior lessons gate; Card Done: agent move on QA-complete + lessons + forward feedback **only** `feature` / `bug` / `agent` / `commit-issue` (Signatures: `card-done-agent-move-qa-complete`, `card-done-forward-feedback` — on card after Lessons captured; top-3 in chat — §7 Card Done); registry + **`docs/`**; AC `[x]` before Review; **GovernanceCompact** Card Done: cite `--line-counts` before/after (Signature: `governance-compact-baseline`); **§6:** ≥1 skill + ≥1 rule |
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
| Ruff E501 on touched `.py` | **Run** `.venv/bin/ruff check --select E501` on every edited `.py`/`.pyi` path before handoff — not optional; hook 1 blocks commit (Signature: `ruff-e501-line-length`) |
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

**Read-only / Ask turns:** run the §6 mental check (both questions); **file edits optional**.
Handoff: one line each — `Skills updated: none (read-only)` / `Rules updated: none (read-only)`.
Edit only when the learning is urgent and durable.

If a learning applies on **implementation** turns → **edit in the same turn** before handoff. Do not only promise to update later.

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
| Kanban card types / sections | [kanban-markdown](../kanban-markdown/SKILL.md) | [kanban-bug-cards.mdc](../../rules/kanban-bug-cards.mdc), [kanban-inquiry-cards.mdc](../../rules/kanban-inquiry-cards.mdc), [kanban-agent-cards.mdc](../../rules/kanban-agent-cards.mdc) |
| Where code lives, save targets, layout | [repo-map](../repo-map/SKILL.md) | — |
| Which tests to run, catalog counts, Qt sandbox | [targeted-testing](../targeted-testing/SKILL.md) | [testing.mdc](../../rules/testing.mdc) if hook-level |
| Ruff / palette / pytest hook order | [pre-commit-workflow](../pre-commit-workflow/SKILL.md) | — |
| Panel/dialog/grid wiring | [ui-change](../ui-change/SKILL.md) | [ui-dialogs.mdc](../../rules/ui-dialogs.mdc), [ui-panels.mdc](../../rules/ui-panels.mdc), etc. |
| Cross-cutting failure pattern | [reference.md](reference.md) § Common failure patterns (§6f row) | Owning area `.mdc` — cite **Signature** only; no duplicate fix prose |
| Self-eval not run / skipped | This skill | [agent-self-evaluation.mdc](../../rules/agent-self-evaluation.mdc) |
| Governance artifact drift (AGENTS.md, triage, reference, rules) | [agent-triage](../agent-triage/SKILL.md) | [agent-consistency.mdc](../../rules/agent-consistency.mdc); self-eval **§6g** on governance edits |
| Missing Files used / Context load in handoff | This skill §7 | [agent-self-evaluation.mdc](../../rules/agent-self-evaluation.mdc) |
| [AGENTS.md](../../AGENTS.md) routing drift | [agent-triage](../agent-triage/SKILL.md) | [agent-routing.mdc](../../rules/agent-routing.mdc); update AGENTS.md |
| Edit `agent-*` / `kanban-*` skills | Read AGENTS.md § Maintaining before handoff | — | [agent-agents-md-maintenance.mdc](../../rules/agent-agents-md-maintenance.mdc) |

Prefer **`reference.md`** for examples, path→test rows, and failure-pattern tables.  
Prefer **`SKILL.md`** for procedures; prefer **`.mdc`** when the learning is a hard constraint on future edits in a file glob.

### 6c. What to add

**Consolidate-before-expand (implementation turns):** Before adding skill or rule prose, **grep**
the target for an existing row or bullet. Prefer a [reference.md](reference.md) §6f row or merge
into an existing bullet over new paragraphs. At **~15 lines** of accumulated tips in one section,
**consolidate** or move detail to `reference.md` — do not append without grepping first. Signature:
`governance-compact-self-eval-handoff`.

**Recurring failures:** add a row to [reference.md](reference.md) § Common failure patterns per **§6f** — do not duplicate **Fix pattern** prose in this skill or in rules.

Good additions (durable, generalizable):

- "When X fails, check Y first"
- Path → test row missing from pre-commit map
- New cross-cutting failure row (grep **Signature** first — §6f)
- Sandbox/permission note for a test class
- Hook-specific fix order
- New kanban label type → scoped rule or row in existing kanban rule

Bad additions (skip):

- Restating code that changes every week
- Long prose or duplicate of an existing reference row
- Task-specific variable names with no reuse
- Entire conversation summaries
- Same bullet in both a skill and a rule

### 6d. How to edit

1. **Grep before add** — search target skill, rule, and `reference.md`; do not duplicate rows.
2. **Minimal diff** — one table row, one bullet, or one short subsection.
3. **Concrete** — name files, tests, commands, or rule paths; avoid vague advice.
4. **Consolidate at ~15 lines** — merge or move to `reference.md` before expanding a section.
5. Rules: keep `description` and `globs` accurate; use `alwaysApply: true` only for cross-cutting mandates.

### 6e. When to skip file edits

| Turn type | Skills | Rules |
| --------- | ------ | ----- |
| **Implementation / fix / refactor** | **Required** — ≥1 edit | **Required** — ≥1 edit |
| Read-only / Ask | Optional — `none (read-only)` | Optional — `none (read-only)` |
| User forbids skill/rule changes | `none (user requested)` | `none (user requested)` |
| Learning uncertain | Rare on implementation — prefer a small rule reminder over skipping | Same |

### 6f. Failure pattern row schema

Canonical table: [reference.md](reference.md) § Common failure patterns. One row per cross-cutting mistake that recurs across areas.

| Column | Content |
| ------ | ------- |
| **Signature** | Stable lowercase kebab-case grep key; optional area prefix (e.g. `palette-hardcoded-count`, `yaml-stage1-structure-yaml`) |
| **Trigger snippet** | Short grep-friendly symptom (path, log line, handoff field) |
| **Fix pattern** | One-line what to do instead — **only** here and in the owning skill workflow, not copied into `.mdc` |
| **Skill** | Owning skill slug for procedure detail |
| **Rule** | Owning `.mdc` if a path-scoped constraint applies; `—` if skill-only |

**Lookup:** `Grep` **Signature** or **Trigger snippet** per [agent-triage/SKILL.md](../agent-triage/SKILL.md) §1b and [reference.md](../agent-triage/reference.md) § Failure pattern routing (on failure signals only). Churn review: self-eval §6 when no row matches but failure recurs.

### 6g. Consistency checks (governance paths only)

**Not every turn.** Run before handoff when this turn **edited** any path in [agent-consistency.mdc](../../rules/agent-consistency.mdc) `globs` (`AGENTS.md`, `.cursor/skills/agent-*/`, `.cursor/skills/kanban-*/`, `.cursor/rules/agent-*.mdc`, `.cursor/rules/kanban-*.mdc`).

Ask yes/no; any **yes** → update in the **same turn** or flag **AGENTS.md stale** / **Context load** note:

| Question | If yes, update |
| -------- | -------------- |
| Did routing or turn lifecycle change? | [AGENTS.md](../../AGENTS.md) Every turn / Classify + [agent-routing.mdc](../../rules/agent-routing.mdc) + [agent-triage/SKILL.md](../agent-triage/SKILL.md) |
| Did triage classify, §1b, or failure routing change? | [agent-triage/SKILL.md](../agent-triage/SKILL.md) + [agent-triage/reference.md](../agent-triage/reference.md) + AGENTS.md as needed |
| Did a failure **Signature** or reference row change? | Owning `reference.md` + triage failure routing + rules (Signature cite only) |
| Did a kanban **label** or card workflow change? | AGENTS.md card types + `kanban-*.mdc` + [kanban-markdown/SKILL.md](../kanban-markdown/SKILL.md) |
| Did agent/kanban **rules** change? | AGENTS.md area table + peer rules per [agent-consistency.mdc](../../rules/agent-consistency.mdc) |
| Did user-facing agent workflow in **docs** change? | [docs/governance/](../../docs/governance/) handbook + [development.md](../../docs/development.md) product setup per [docs-maintenance](../docs-maintenance/SKILL.md) — Signature: `docs-governance-split` |

**Detail checklist** (four check types + registry): [agent-consistency.mdc](../../rules/agent-consistency.mdc) — do not duplicate that prose here. **Artifact parity:** [agent-triage/reference.md](../agent-triage/reference.md) § Consistency matrix.

**Drift alerts (required when governance edited):** After the yes/no table, compare matrix rows for artifacts you touched. If parity is **not** fixed in the same turn, list one line per mismatch using prefixes from [agent-triage/reference.md](../agent-triage/reference.md) § **Drift alert examples** — optional `[info|warn|critical]` prefix (default **`warn`** when omitted) — in **Context load**, §6g notes, and handoff `- **Drift alerts:**`. **Or** when the user approved temporary drift: `KNOWN_DRIFT: <artifact pair> — <reason>[; expires: <date or note>]` (see reference § KNOWN_DRIFT).

**Manual compare:** grep matrix anchors or run `python3 scripts/check_governance_parity.py` — paste stdout into Context load / §6g / `- **Drift alerts:**`.

**Read-only / no governance edits:** §6g and drift alerts → N/A.

**Do not skip the handoff block or the §6 questions** — only skip file writes on read-only turns or explicit user opt-out.

## 7. Handoff format (required every turn)

Signature: `governance-compact-self-eval-handoff`. **Last sections only** — in order:

1. **`### Top forward feedback`** — **Card Done turns only** (`feature` / `bug` / `agent` /
   `commit-issue`): up to three items from the card block (Primary + top Secondary; backfill per
   [kanban-markdown/reference.md](../kanban-markdown/reference.md) § Forward-looking feedback).
   Agent moves card to `done/` same turn (Signature: `card-done-agent-move-qa-complete`). Omit on
   all other turns.
1b. **`### Forward feedback dedup`** — **Card Done turns only** when
   `build_forward_feedback_index.py` stderr reports exact duplicate question fingerprints (Signature:
   `forward-feedback-card-done-ingest`). Non-blocking; place after **`### Top forward feedback`**
   when both apply. Omit when no dedup warnings.
2. **`### Epic summary`** or **`### Initiative summary`** — **epic audit / archive group complete
   turns only:** 1–2 paragraphs, outcomes in plain language ([kanban-markdown/reference.md](../kanban-markdown/reference.md)
   § Epic / initiative completion summary; Signature: `governance-epic-completion-summary`). Epic
   audit → **`### Epic summary`**; archive group complete → **`### Initiative summary`**. Omit on
   all other turns.
2b. **`### Compaction advisory`** — **every turn** when `python3 scripts/check_governance_parity.py
   --compaction --quiet` reports **warn** or **critical** (Signature:
   `governance-compaction-drift-alert`). Fixed template:

```markdown
### Compaction advisory
- **Status:** consider compaction | compaction urgent
- **Severity:** warn | critical
- **Signals:** gc0 +N% (current/baseline); always-on governance +N%; top outlier …
- **Action:** [audit-and-compaction.md](../../docs/governance/audit-and-compaction.md); `--compaction`; **AgentContextBudget** epic
```

   Map **warn** → `consider compaction`; **critical** → `compaction urgent`. **Omit** entire section
   when below warn. Pair with **Compaction** field in **Self-evaluation** (not `none` when this block
   is present).
3. **`### Files used`** — load order; one line per path/skill that drove the turn
4. **`### Self-evaluation`** — compact fields below; **do not** paste §1–§6 checklists

Detail: §2b (context load), §6 (skill/rule loop), §6g (governance drift). **Parity:** `check_handoff_duplication_pair` flags when AGENTS End handoff repeats ≥3 consecutive compact field lines (Signature: `governance-gc7-handoff-duplication-pair`). More examples:
[reference.md](reference.md) § Example handoffs.

### Files used

Tag `(grep)`, `(read)`, `(edit)`, `(write)` when the same path appears twice. Omit grep-only
hits that did not drive decisions.

### Self-evaluation (compact — one line per field)

Expand a field only when that check **failed** or needs a drift line.

```markdown
### Self-evaluation
- **Scope:** on-target | read-only | note
- **Context load:** ok | note — AGENTS.md current|updated|stale: …
- **Compaction:** none | consider — one line | urgent — one line
- **Drift alerts:** none (N/A) | `[severity]` + prefix | KNOWN_DRIFT: …
- **Tests:** path + result | n/a — why
- **Docs:** paths | n/a — why
- **Skills used:** slugs | none
- **Skills updated:** slug — one line | none (read-only) | none (user requested)
- **Rules updated:** path — one line | none (read-only) | none (user requested)
- **Commit-ready:** yes | needs pre-commit | n/a
```

**Read-only:** §6 mental check still required; `Skills updated` / `Rules updated` →
`none (read-only)` unless urgent durable learning.

**Implementation:** `Skills updated` and `Rules updated` must name edits — not `none` (§6e).

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
