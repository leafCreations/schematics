# Audit and compaction

## Periodic governance audit

**Primary cadence:** when a multi-card epic completes, the agent runs § Epic audit on the anchor
card (user confirms no active cards for that `epic:`). Procedure:
[kanban-markdown/reference.md](../../.cursor/skills/kanban-markdown/reference.md) § Epic audit.
CLI: `python3 scripts/resolve_epic_cards.py --epic {Name} --status`; closed names in
[epics-closed.yaml](../epics-closed.yaml). Signature: `governance-epic-completion-audit`. On the audit
turn, emit **`### Epic summary`** in chat (1–2 paragraphs, outcomes not paths) and optional
**`## Summary`** on the anchor — [kanban-markdown/reference.md](../../.cursor/skills/kanban-markdown/reference.md)
§ Epic / initiative completion summary; Signature: `governance-epic-completion-summary`.

**Archive group (gel3):** when a feature spans multiple epics, epic audit and batch archive are
separate gates. Per-epic audit may run when that `epic:` has no active cards; **do not** move
members to `archived/` until the user confirms the **archive group** is complete. Manifest SSOT:
anchor card **`## Archive group: {Name}`** table; members carry matching `archiveGroup:` frontmatter.
Procedure: [kanban-markdown/reference.md](../../.cursor/skills/kanban-markdown/reference.md) § Archive group.
CLI: `python3 scripts/resolve_archive_group.py --group {Name} --status`. Card Done moves to `done/`
only — never archive on the same turn. Signature: `governance-archive-group-batch`. On the batch
turn, emit **`### Initiative summary`** in chat and optional **`## Summary`** on the anchor —
reference § Epic / initiative completion summary; Signature: `governance-epic-completion-summary`.

**Single-card archive (gel5):** one-off cards (`epic: null`, no `archiveGroup:`) in **`done/`** move
to `archived/` on user **`archive @card`** / **`archive card {id}`** — not on Card Done, not gel3
batch. Procedure: reference § Single-card archive. CLI:
`python3 scripts/move_kanban_card.py --id {id} --to archived`. Move-only — no lessons. Signature:
`governance-single-card-archive`.

**Optional backstop** (suggested quarterly or ~90 days without an epic close):

```bash
python3 scripts/create_governance_audit_card.py
python3 scripts/create_governance_audit_card.py --epic GovernanceEpicLifecycle  # status only hint
```

Full procedure: [kanban-markdown/SKILL.md](../../.cursor/skills/kanban-markdown/SKILL.md) § Periodic
AGENTS.md governance audit. Options: `--date YYYY-MM-DD`, `--force` to overwrite same-day card.

Checklist summary:

1. AGENTS.md Every turn ↔ agent-triage ↔ agent-routing.mdc
2. Card types ↔ kanban-*.mdc ↔ kanban-markdown
3. Failure-pattern Signatures ↔ reference tables ↔ [Consistency matrix](../../.cursor/skills/agent-triage/reference.md#consistency-matrix)
4. `feature-areas.yaml` `handlers:` (malformed, cross-area duplicates) ↔ kanban **Product Methods** on open cards (legacy **Label Methods** still parsed)
5. Handoff format ↔ agent-self-evaluation §7
6. `docs/governance/` handbook ↔ AGENTS.md + consistency links; optional
   `python3 scripts/check_governance_parity.py --docs-governance-split` (Signature: `docs-governance-split`)
7. Lessons coverage: `python3 scripts/check_lessons_coverage.py` when `.devtool/features/done/` exists; composite &lt; 75% should match `check_governance_parity.py` `Lessons coverage drift alert:` output

Record drift on the audit card **## Audit findings**; spawn fix cards per bullet — do not fix silently during the audit turn.

## Governance compaction (gc0 baseline)

Epic **GovernanceCompact** — measure token churn before shrinking skills/rules. Signature: `governance-compact-baseline`.

**Report (on demand):**

```bash
python3 scripts/check_governance_parity.py --line-counts
```

Prints artifact line counts (sorted), named duplication-pair section sizes, and all `alwaysApply: true` rules with a governance vs other tag. Exit **0** — informational only; does not run parity checks or spawn drift cards.

**Baseline table (2026-06-27 snapshot)** — regenerate with `--line-counts` after gc1+ edits:

| Artifact | Lines | Notes |
| -------- | ----- | ----- |
| `.cursor/skills/kanban-markdown/SKILL.md` | 341 | Lifecycle + gates (gc1 — was 1171) |
| `.cursor/skills/kanban-markdown/reference.md` | 525 | Card templates + audit detail (gc1) |
| `.cursor/skills/agent-self-evaluation/SKILL.md` | 309 | Handoff §7 compact + §6c consolidate gate (gc4) |
| `.cursor/skills/agent-triage/reference.md` | 246 | Consistency matrix + failure routing |
| `AGENTS.md` | 203 | Entry routing + Classify quickly (gc4 End handoff pointer) |
| `.cursor/skills/agent-triage/SKILL.md` | 209 | Turn lifecycle §1 |
| `kanban-*.mdc` (8 files) | 456 | Sum — card-type scoped rules |
| `agent-*.mdc` (4 files) | 211 | Sum — routing / self-eval / consistency |
| **Baseline total** | **2531** | 18 files in `GOVERNANCE_COMPACT_BASELINE_GLOBS` (gc1 + reference.md) |

**acb3 (2026-06-28 — `governance-thin-agents-md`):** `AGENTS.md` **162** lines — Maintaining table
replaced with pointer rows to [agent-consistency.mdc](../../.cursor/rules/agent-consistency.mdc) and
reference § Closed epics; epic narrative removed from Maintaining.

**acb4 (2026-06-28 — `governance-index-not-grep`):** yaml-first done/archived routing — hard ban in
reference § Discovery ladder Kanban branch; detail in [kanban-markdown/reference.md](../../.cursor/skills/kanban-markdown/reference.md)
§ Index vs folder grep; parity gate `check_index_not_grep_routing`.

**acb5 (2026-06-28 — `governance-discovery-ladder`):** single classify → task type → grep tree in
[agent-triage/reference.md](../../.cursor/skills/agent-triage/reference.md) § Discovery ladder (mermaid);
[agent-routing.mdc](../../.cursor/rules/agent-routing.mdc) Discovery budget is pointer-only;
`check_discovery_ladder_routing` — `pytest -k acb5`.

**Duplication pairs** (section line counts — same prose maintained in multiple places):

**Automated gc7 check:** `check_handoff_duplication_pair` in `check_governance_parity.py` fails when
AGENTS ``## End handoff`` repeats ≥3 consecutive `- **Field:**` lines verbatim from
`agent-self-evaluation/SKILL.md` §7 compact template (pointer-only gc4 — not cross-reference lines).
Signature: `governance-gc7-handoff-duplication-pair`.

**Advisory gc7 forward-feedback audit:** `check_governance_parity.py --forward-feedback-audit`
audits **present** parent `## Forward-looking feedback` blocks only (field gaps on written
categories; no six-category mandate — fcp3). Optional Risk 5 check: parent close with Risk 5 in ff
block should link a **`feedback`** spawn under **`## Spawned follow-up cards`**. Exit 0 —
complements C1b (lessons required; parent ff optional). Signature:
`governance-gc7-forward-feedback-audit`. **Advisory ff3 stale metrics:**
`--forward-feedback-stale` reports high-risk open index rows with no spawn after N days (default
30); exit 0 — complements gc7 (card fields) and `resolve_forward_feedback.py --report` (category /
risk-band counts). Signature: `forward-feedback-stale-metrics`.

| Pair | Lines (approx.) | gc1+ action |
| ---- | --------------- | ----------- |
| Classify quickly (`AGENTS.md`) | 21 | gc2 — ≤5-row summary; reference § Classify canonical |
| Classify §1 (`agent-triage/SKILL.md`) | 51 | gc2 — pointer only; no duplicate table |
| Classify signals (`reference.md`) | 23 | gc2 — canonical full signal table |
| AGENTS `### Card types` | 14 | Link to kanban rules; drop prose |
| `kanban-markdown/SKILL.md` (lifecycle) | 341 | gc1 complete — card detail in reference.md |
| `kanban-markdown/reference.md` | 525 | gc1 — templates, examples, audit checklist |
| `kanban-*.mdc` (sum) | 456 | Scoped load — keep; dedupe from skill |

**Always-on rules** (`alwaysApply: true`):

| Rule | Lines | Tag |
| ---- | ----- | --- |
| `.cursor/rules/agent-routing.mdc` | 105 | governance |
| `.cursor/rules/kanban-card-gates.mdc` | 92 | governance |
| `.cursor/rules/agent-self-evaluation.mdc` | 51 | governance (gc4 — §7 pointer) |
| **Total** | **248** | **248** governance-related |

**acb2 (2026-06-28 — `governance-always-on-rule-diet`):** `worldgen.mdc`, `model-routing.mdc`, and
`testing.mdc` are **glob-scoped** (`alwaysApply: false`) — not in the table above. Path→test rows
live in [targeted-testing/reference.md](../../.cursor/skills/targeted-testing/reference.md). Prior
gc0 snapshot (2026-06-27) for comparison:

| Rule | Lines | Tag |
| ---- | ----- | --- |
| `.cursor/rules/testing.mdc` | 164 | governance |
| `.cursor/rules/agent-routing.mdc` | 79 | governance |
| `.cursor/rules/kanban-card-gates.mdc` | 60 | governance |
| `.cursor/rules/worldgen.mdc` | 58 | other |
| `.cursor/rules/model-routing.mdc` | 57 | other |
| `.cursor/rules/agent-self-evaluation.mdc` | 38 | governance |
| **Total** | **462** | **347** governance-related |

**Success criteria → measurable signals** (parent inquiry: reduce governance token churn):

| Goal | Signal | Tool / gate |
| ---- | ------ | ----------- |
| Smaller always-on surface | Governance always-on line count ↓ | `--line-counts`; gc3 toggles `alwaysApply` |
| Less duplicated prose | Classify trio + kanban skill/rule sum ↓ | `--line-counts` duplication pairs |
| Routing stays correct | Zero drift alerts | `check_governance_parity.py` exit 0 |
| Agents still hand off | `### Files used` + `### Self-evaluation` every turn | `agent-self-evaluation.mdc` (always-on) |
| Registry parity | `handlers:` + schema keys aligned | `check_area_schema_parity`, `--agents-parity` |

gc1+ cards set explicit line-count targets from this baseline; gc3 completes scoped card-type rule load.

**gc3 — kanban rule globs (complete):** Card-type `kanban-*-cards.mdc` use
`globs: .devtool/features/**/*.md` and `alwaysApply: false` (landed with gc1; gc3 validates +
documents). [kanban-card-gates.mdc](../../.cursor/rules/kanban-card-gates.mdc) remains always-on.
[agent-triage/SKILL.md](../../.cursor/skills/agent-triage/SKILL.md) §1 — after label gate, load
**exactly one** scoped card-type rule per `labels` (mapping in [agent-routing.mdc](../../.cursor/rules/agent-routing.mdc)
§ Kanban card type; not all `kanban-*.mdc`). Signature:
`governance-compact-kanban-rule-globs`; enforced by `check_kanban_rule_globs` in
`check_governance_parity.py`.

**Manual QA (gc3):** In Cursor chat, `@`-attach a **bug** card under `.devtool/features/` and
confirm bug-card constraints still apply (e.g. **Corrective Action** not **Decisions**). Repeat for
one **agent** card if glob behavior is uncertain. If Cursor ignores rule globs, keep
`alwaysApply: true` on card-type rules and note the waiver on the card — compaction falls back to
gc1/gc2 prose reduction only.

**gc6 — classify task types (complete):** After prompt-verb / card gate, agents route by work kind
(governance, docs-only, code, refactor, inquiry, multi-file, rule/skill) via
[agent-triage/reference.md](../../.cursor/skills/agent-triage/reference.md) § **Task types** — Signature:
`governance-compact-classify-task-types`. Task types live under reference § Classify (subsection);
not AGENTS summary rows.

**gc2 — Classify SSOT (complete):** Full signal table in reference § Classify only — Signature:
`governance-compact-classify-ssot`. AGENTS § Classify quickly ≤5-row summary; triage §1 pointer;
`check_classify_parity` enforces fingerprint, anchor coverage, and summary caps.

**gc4 — self-eval handoff compaction (complete):** Canonical compact handoff in
[agent-self-evaluation/SKILL.md](../../.cursor/skills/agent-self-evaluation/SKILL.md) §7 — Signature:
`governance-compact-self-eval-handoff`. AGENTS End handoff and
[agent-self-evaluation.mdc](../../.cursor/rules/agent-self-evaluation.mdc) point to §7 (no duplicate
full template). Read-only turns: §6 mental check + one-line `none (read-only)` handoff fields.
Implementation: grep + consolidate-before-expand gate (§6c/§6d).

**gc5 extension (forward-feedback tightening):** After gc5 baseline, reference § Forward-looking
feedback adds **Impact Scope**, **References**, **Mitigation** on max-tier items, **Importance**
when ≥2 items share max risk, and top-3 chat surfacing on Card Done turns — Signature stays
`card-done-forward-feedback`; legacy done cards without new fields remain valid.

## AgentContextBudget epic (acb0) — closed 2026-06-28

Epic **AgentContextBudget** — reduce governance token churn and agent discovery waste without
breaking kanban parity. **Closed** — anchor archived:
`.devtool/features/archived/agent-agent-context-budget-acb0-schema-spec-2026-06-30.md`.
Registry: [epics-closed.yaml](../epics-closed.yaml). Follow-up: **KanbanReferenceThin** (closed).
Follows closed **GovernanceCompact** (gc0–gc8) and **ForwardFeedbackCapturePolicy**.

### Six concern areas (user 2026-06-30)

| # | Concern | Phase | Signature |
| - | ------- | ----- | --------- |
| 1 | Always-on rule diet — scope `worldgen.mdc`, `model-routing.mdc`, `testing.mdc` with globs | acb2 | `governance-always-on-rule-diet` |
| 2 | done/archived growth — yaml indexes + scripts, not folder grep | acb4 | `governance-index-not-grep` |
| 3 | Thin AGENTS.md — trim § Maintaining; pointer to `epics-closed.yaml` + reference | acb3 | `governance-thin-agents-md` |
| 4 | Hard index-not-grep — route through `lessons-index.yaml`, `forward-feedback-index.yaml`, `resolve_prior_lessons.py` | acb4 | `governance-index-not-grep` |
| 5 | Discovery ladder — classify → area → grep decision tree | acb5 | `governance-discovery-ladder` |
| 6 | Duplication automation | acb6 | `governance-duplication-automation` |

### Epic phases

| order | phase | scope | Signature |
| ----- | ----- | ----- | --------- |
| acb0 | schema | Six areas + epic table | — |
| acb1 | compaction threshold | `--compaction`, handoff advisory | `governance-compaction-drift-alert` |
| acb2 | always-on diet | Product rules off default context | `governance-always-on-rule-diet` |
| acb3 | thin AGENTS.md | Maintaining table trim | `governance-thin-agents-md` |
| acb4 | index-not-grep | yaml-first done/archived routing | `governance-index-not-grep` |
| acb5 | discovery ladder | classify → area → grep tree | `governance-discovery-ladder` |
| acb6 | duplication automation | post-thinning gc7 extension | `governance-duplication-automation` |

**Implement order:** acb1 → acb2 → acb3 → acb4 → acb5 → acb6 (all landed; epic archived).

**Baseline SSOT:** [compaction-baseline.yaml](compaction-baseline.yaml) (gc0 line counts from 2026-06-27;
refresh after epic closes).

## Compaction threshold notifications (acb1)

Epic **AgentContextBudget** — Signature: `governance-compaction-drift-alert`.

**Baseline SSOT:** [compaction-baseline.yaml](compaction-baseline.yaml) (gc0 line counts from 2026-06-27;
refresh after epic closes).

**Check:**

```bash
python3 scripts/check_governance_parity.py --compaction
python3 scripts/check_governance_parity.py --compaction --spawn-cards   # critical only
```

Exit **0** — advisory. Agents run `--compaction --quiet` before handoff; when **warn** or
**critical**, emit **`### Compaction advisory`** per
[agent-self-evaluation/SKILL.md](../../.cursor/skills/agent-self-evaluation/SKILL.md) §7.

| Tier | Signal | Threshold |
| ---- | ------ | --------- |
| **warn** | gc0 artifact total | > baseline + **15%** |
| **critical** | gc0 artifact total | > baseline + **25%** |
| **warn** | always-on governance lines | > **400** or > baseline + **15%** |
| **critical** | always-on governance lines | > **480** or > baseline + **25%** |
| **warn** | single gc0 artifact | > baseline + **20%** or > **600** lines |
| **critical** | single gc0 artifact | > baseline + **50%** or > **900** lines |
| **warn** | duplication `kanban-markdown reference` | > **700** lines |
| **critical** | duplication `kanban-markdown reference` | > **1000** lines |
| **warn** | duplication `kanban-*.mdc` sum | > **600** lines |
| **critical** | duplication `kanban-*.mdc` sum | > **800** lines |
| **warn** | duplication `classify trio (sum)` | > **80** lines |
| **critical** | duplication `classify trio (sum)` | > **120** lines |
| **warn** | duplication `kanban lifecycle (sum)` (SKILL + reference) | > **900** lines |
| **critical** | duplication `kanban lifecycle (sum)` | > **1200** lines |

**Spawn:** `--spawn-cards` creates one **agent** todo under epic **AgentContextBudget** on
**critical** only (`agent-governance-compaction-advisory-YYYY-MM-DD`).

**Stale spawns:** close pre-refresh compaction todos **Superseded** when `--compaction --quiet` is
**ok** after baseline refresh — Signature: `governance-compaction-drift-alert`.

### Duplication threshold automation (acb6)

**Signature:** `governance-duplication-automation`. Extends gc7 handoff pair check with
post-compaction caps on Classify trio and kanban lifecycle pairs (reference + SKILL sum).

```bash
python3 scripts/check_governance_parity.py --duplication-threshold
python3 scripts/check_governance_parity.py --duplication-threshold --spawn-cards
```

Exit **1** when any pair exceeds **warn** or **critical** caps in
[compaction-baseline.yaml](compaction-baseline.yaml) (`duplication_pairs` + `thresholds`).
`--spawn-cards` creates **agent** todo under **AgentContextBudget** on **warn+**
(`agent-governance-duplication-threshold-YYYY-MM-DD`). Pair with `--line-counts` for raw section
sizes; `--compaction` remains advisory (exit 0).

**Stale spawns:** close pre-thinning or pre-refresh todos **Superseded** when `--duplication-threshold
--no-spawn-cards` exits **0** — link [acb6 archived](../../../.devtool/features/archived/agent-agent-context-budget-acb6-duplication-automation-2026-06-30.md)
+ KanbanReferenceThin krt3; Signature: `governance-duplication-automation`.

**CI / default parity:** `--duplication-threshold` is **not** in default `run_checks` — opt-in audit
(Signature: `governance-thin-kanban-reference`; KanbanReferenceThin closed 2026-06-28).

### KanbanReferenceThin epic (krt0–krt3) — closed 2026-06-28

**Signature:** `governance-thin-kanban-reference`. Thin `kanban-markdown/reference.md` to pass
absolute duplication caps without relaxing thresholds. **Closed** — anchor archived:
`.devtool/features/archived/agent-kanban-reference-thin-krt0-schema-spec-2026-06-30.md`.
Registry: [epics-closed.yaml](../epics-closed.yaml).

**Duplication caps (unchanged — forcing function):**

| Threshold key | warn | critical |
| ------------- | ---- | -------- |
| `duplication_reference_critical` | 700 | **1000** |
| `kanban_lifecycle_critical` | 900 | **1200** |

**Baseline snapshot (2026-06-30, post-krt3):** reference **551** lines (−1035 vs krt0 **1586**);
kanban lifecycle (sum) **897** (−1174 vs krt0 **2071**); `--duplication-threshold` exit **0**.
`reference-glossary.md` holds glossary SSOT; classify trio **62** after triage §1 / Task types split.

| Phase | Card | Scope | status |
| ----- | ---- | ----- | ------ |
| krt0 | `agent-kanban-reference-thin-krt0-schema-spec-2026-06-30` | Epic table + caps SSOT | archived |
| krt1 | _(feedback implement 2026-06-30)_ | Closed epic spawn tables + dg1 → pointers | done (−194 lines) |
| krt2 | `agent-kanban-reference-thin-krt2-legacy-ff-trim-2026-06-30` | Card Done / ff cadence dedupe | archived |
| krt3 | `agent-kanban-reference-thin-krt3-glossary-trim-2026-06-30` | § Kanban card sections glossary trim | archived |

**Closed:** gel0 2026-06-28 — archive group retired.
