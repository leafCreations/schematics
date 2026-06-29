# Forward feedback index

Generated SSOT for gc5 **questions** on closed cards — separate from
`docs/lessons-index.yaml` (lessons = promoted artifacts; forward feedback = open questions).
Signature: `forward-feedback-index`.

| Field | Meaning |
| ----- | ------- |
| `version` | Schema version (`1`) |
| `generated_at` | ISO-8601 UTC timestamp from last generator run |
| `items[].id` | Stable `ff-*` uid (source card + category + seq + question fingerprint) |
| `items[].source_card` | Relative path to done/archived card |
| `items[].category` | gc5 category (Governance, Skill, Rule, Codebase, Prompt pattern, Routing) |
| `items[].question` | Question text from Card Done block |
| `items[].status` | Resolution state — `open`, `discussing`, `answered`, `spawned`, `deferred`, `wont-fix`, `duplicate` |
| `items[].spawned` | List of spawned kanban card paths (repo-relative) |
| `items[].resolution` | Free-text resolution note |
| `items[].answered_at` | ISO date when marked answered |
| `items[].duplicate_of` | Canonical `ff-*` id when another item shares the exact question fingerprint (advisory — ff1) |
| `items[].risk_level` / `impact_scope` / `importance` | Ranking fields when present on card |

Build and query:

```bash
python3 scripts/build_forward_feedback_index.py
python3 scripts/build_forward_feedback_index.py --check   # exit 1 when stale
python3 scripts/resolve_forward_feedback.py --category Codebase --status open --top 3
python3 scripts/resolve_forward_feedback.py --category rules --top 3   # alias → Rule
python3 scripts/resolve_forward_feedback.py --report
python3 scripts/resolve_forward_feedback.py --report --stale-days 30
python3 scripts/resolve_forward_feedback.py --link ff-example-id --card .devtool/features/inquiry-foo.md
python3 scripts/resolve_forward_feedback.py --id ff-example-id --set-status answered --resolution "closed in chat"
```

**Open backlog metrics (ff3):** `resolve_forward_feedback.py --report` prints open counts by gc5
category and risk band (high ≥4, medium 3, low 1–2, unknown). Optional `--stale-days N` adds an
advisory subsection for high-risk open items with no `spawned[]` link older than N days since
`completed_at` (default threshold N=30 on parity flag only). Signature:
`forward-feedback-stale-metrics`.

**Resolution lifecycle (ff2):** manual/CLI first — no auto-sync from kanban card status. Default
`--status open` queries exclude `spawned`, `duplicate`, and rows with `duplicate_of` unless
`--include-spawned` / `--include-duplicates`. Linking a spawned card sets `status=spawned` and
appends the path to `spawned[]`. Index rebuild preserves overlay fields — Signature:
`forward-feedback-resolution-tracking`.

**Ranking (within category):** risk descending → impact scope (system-wide > multi-card > local) →
Importance (Primary > Secondary > Tertiary) → `completed_at` tie-break. Default `--status open`
excludes spawned unless `--include-spawned`.

**Card Done (ff1):** after `build_lessons_index.py` when lessons ran, run
`python3 scripts/build_forward_feedback_index.py`. Ingests legacy parent
`## Forward-looking feedback` on closed cards **and** **`feedback`**-labeled cards (todo/review/done/
archived) with **`## Risk assessment`** (fcp2). Exact duplicate question fingerprints set
`duplicate_of` on later items and emit stderr warnings — surface in chat as
`### Forward feedback dedup` (non-blocking). Signature: `forward-feedback-card-done-ingest`.

**Feedback spawn path (fcp2):** on parent Card Done, spawn **`feedback`** todo when risk **≥ 3**
(**Risk 5** mandatory — Option A). After index rebuild, link child **Context** and resolution:

```bash
python3 scripts/build_forward_feedback_index.py
python3 scripts/resolve_forward_feedback.py --link ff-{stem}-… --card .devtool/features/feedback-….md
```

When the user answers a **`feedback`** card, mark index row answered:

```bash
python3 scripts/resolve_forward_feedback.py --id ff-{id} --set-status answered --resolution "closed in chat"
```

Signature: `forward-feedback-resolution-tracking`, `card-done-feedback-spawn`.

**Cadence (ForwardFeedbackCapturePolicy fcp2):** parent **lessons always**; **no** mandatory parent
six-category ff on new closes. **`feedback`** cards are primary index ingest; legacy parent gc5 on
archived cards preserved. **C1b** parent ff optional (fcp3) — Signature:
`forward-feedback-capture-policy`, `lessons-coverage-c1b-forward-feedback`.

| Index ingest source | When |
| ------------------- | ---- |
| **`feedback`** card (`## Risk assessment`) | todo / review / done / archived (fcp2) |
| Legacy parent **`## Forward-looking feedback`** | closed cards (archived; no mass migration) |
| Anchor **`## Epic coordination`** | **Never** |

Full capture policy:
[kanban-markdown/reference.md § Forward-feedback capture cadence](../../.cursor/skills/kanban-markdown/reference.md#forward-feedback-capture-cadence)
— Signatures: `forward-feedback-capture-policy`, `epic-coordination-not-forward-feedback`.

Complements `check_governance_parity.py --forward-feedback-audit` (gc7 field completeness on cards —
not backlog SSOT; present-parent-ff field audit only). Signature:
`governance-gc7-forward-feedback-audit`. **ff3 stale metrics:**
`check_governance_parity.py --forward-feedback-stale [--stale-days N]` scans
`docs/forward-feedback-index.yaml` for high-risk open backlog rows without spawn links — advisory
exit 0; complements gc7 (card fields) and `--report` (human-readable depth). Not pre-commit by
default. Signature: `forward-feedback-stale-metrics`.

## Backlog hygiene (fbh0)

After **`KanbanCardCapturePolicy`** closes, run a structured resolution pass on open backlog rows
— Signature: `forward-feedback-backlog-hygiene`. **Do not** hand-edit
`docs/forward-feedback-index.yaml`; use CLI overlays + batch helper.

| Kind | Action | CLI status |
| ---- | ------ | ---------- |
| In-flight epic coordination (transition noise) | Resolved by closed epic / ccp cadence | `answered` or `wont-fix` |
| Semantically duplicate of another item | Keep one canonical `ff-*` | `duplicate` + note canonical id |
| Valid future behavior, still open | Keep or `spawned` to todo card | `open` / `spawned` |
| Prompt pattern answered via spawn | Parent ff `spawned` → child agent card Done | `answered` + `--link` / `--set-status` — Signature: `card-done-disambiguate-multi-review` |
| Low value / placeholder gc5 filler | Drop from backlog | `wont-fix` or `deferred` |
| Exact fingerprint duplicate | ff1 ingest set `duplicate_of` | `status=duplicate` |
| `commit-issue` hook capture | Not durable backlog | `wont-fix` |

**Workflow:**

```bash
python3 scripts/resolve_forward_feedback.py --report          # baseline
python3 scripts/batch_forward_feedback_hygiene.py --dry-run   # preview counts
python3 scripts/batch_forward_feedback_hygiene.py           # apply (load/save once)
python3 scripts/build_forward_feedback_index.py               # refresh; preserve overlays
python3 scripts/resolve_forward_feedback.py --report          # after metrics
```

Cadence rubric: [kanban-markdown/reference.md § Forward-looking feedback cadence](../../.cursor/skills/kanban-markdown/reference.md#forward-looking-feedback-cadence)
— Signatures: `card-done-forward-feedback-cadence`, `kanban-card-section-glossary`. Card:
`.devtool/features/agent-forward-feedback-backlog-hygiene-fbh0-2026-06-29.md`.

## Capture policy (ForwardFeedbackCapturePolicy — closed 2026-06-29)

**Closed** (fcp0–fcp3). Replaces mandatory parent six-category **`## Forward-looking
feedback`** on new Card Done closes with risk-gated **`feedback`** card spawns. Full policy:
[kanban-markdown/reference.md § Forward-feedback capture cadence](../../.cursor/skills/kanban-markdown/reference.md#forward-feedback-capture-cadence)
and [reference-glossary.md § Feedback cards](../../.cursor/skills/kanban-markdown/reference-glossary.md#feedback-cards);
risk rubric: [reference-glossary.md § Risk assessment rubric](../../.cursor/skills/kanban-markdown/reference-glossary.md#risk-assessment-rubric).
Signatures: `forward-feedback-capture-policy`, `feedback-label-kanban`, `card-done-feedback-spawn`,
`forward-feedback-risk-rubric`. **fcp2** expands ingest + Card Done spawn workflow in this file.
