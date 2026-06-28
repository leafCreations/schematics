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

**Duplication pairs** (section line counts — same prose maintained in multiple places):

**Automated gc7 check:** `check_handoff_duplication_pair` in `check_governance_parity.py` fails when
AGENTS ``## End handoff`` repeats ≥3 consecutive `- **Field:**` lines verbatim from
`agent-self-evaluation/SKILL.md` §7 compact template (pointer-only gc4 — not cross-reference lines).
Signature: `governance-gc7-handoff-duplication-pair`.

**Advisory gc7 forward-feedback audit:** `check_governance_parity.py --forward-feedback-audit`
reports gc5 field gaps on post-grandfather closed cards (Impact Scope, References, Mitigation when
risk ≥ 4); exit 0 — complements C1b presence metric. Signature:
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
| `.cursor/rules/testing.mdc` | 164 | governance |
| `.cursor/rules/agent-routing.mdc` | 79 | governance |
| `.cursor/rules/kanban-card-gates.mdc` | 60 | governance |
| `.cursor/rules/worldgen.mdc` | 58 | other |
| `.cursor/rules/model-routing.mdc` | 57 | other |
| `.cursor/rules/agent-self-evaluation.mdc` | 38 | governance (gc4 — §7 pointer) |
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
