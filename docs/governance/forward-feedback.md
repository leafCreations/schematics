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
`python3 scripts/build_forward_feedback_index.py`. Exact duplicate question fingerprints set
`duplicate_of` on later items and emit stderr warnings — surface in chat as
`### Forward feedback dedup` (non-blocking). Signature: `forward-feedback-card-done-ingest`.

Complements `check_governance_parity.py --forward-feedback-audit` (gc7 field completeness on cards —
not backlog SSOT). Signature: `governance-gc7-forward-feedback-audit`. **ff3 stale metrics:**
`check_governance_parity.py --forward-feedback-stale [--stale-days N]` scans
`docs/forward-feedback-index.yaml` for high-risk open backlog rows without spawn links — advisory
exit 0; complements gc7 (card fields) and `--report` (human-readable depth). Not pre-commit by
default. Signature: `forward-feedback-stale-metrics`.
