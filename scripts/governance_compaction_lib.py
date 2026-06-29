"""Governance compaction drift vs compaction-baseline.yaml.

Signature: governance-compaction-drift-alert
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.check_governance_parity import (
    collect_always_apply_rules,
    collect_baseline_artifact_paths,
    collect_duplication_pair_counts,
    line_count_for_path,
)

PREFIX_COMPACTION = "Compaction drift alert:"

DEFAULT_BASELINE_PATH = Path("docs/governance/compaction-baseline.yaml")

CLASSIFY_TRIO_SUM_LABEL = "classify trio (sum)"
KANBAN_LIFECYCLE_SUM_LABEL = "kanban lifecycle (sum)"

SEVERITY_OK = "ok"
SEVERITY_INFO = "info"
SEVERITY_WARN = "warn"
SEVERITY_CRITICAL = "critical"

_SEVERITY_RANK = {
    SEVERITY_OK: 0,
    SEVERITY_INFO: 1,
    SEVERITY_WARN: 2,
    SEVERITY_CRITICAL: 3,
}


@dataclass(frozen=True)
class CompactionSignal:
    label: str
    current: int
    baseline: int | None
    severity: str

    @property
    def pct_over(self) -> float | None:
        if self.baseline is None or self.baseline <= 0:
            return None
        return ((self.current - self.baseline) / self.baseline) * 100.0


@dataclass(frozen=True)
class CompactionReport:
    severity: str
    signals: tuple[CompactionSignal, ...]
    gc0_total: int
    gc0_baseline: int
    always_on_governance: int
    always_on_governance_baseline: int

    def handoff_status(self) -> str:
        if self.severity == SEVERITY_CRITICAL:
            return "compaction urgent"
        if self.severity == SEVERITY_WARN:
            return "consider compaction"
        return "none"

    def summary_line(self) -> str:
        parts = [
            f"gc0 {self._pct(self.gc0_total, self.gc0_baseline)} "
            f"({self.gc0_total}/{self.gc0_baseline})",
            f"always-on governance "
            f"{self._pct(self.always_on_governance, self.always_on_governance_baseline)} "
            f"({self.always_on_governance}/{self.always_on_governance_baseline})",
        ]
        if self.signals:
            top = self.signals[0]
            pct = top.pct_over
            pct_s = f"+{pct:.0f}%" if pct is not None else f"{top.current} lines"
            parts.append(f"top: {top.label} {pct_s}")
        return "; ".join(parts)

    @staticmethod
    def _pct(current: int, baseline: int) -> str:
        if baseline <= 0:
            return f"{current} lines"
        pct = ((current - baseline) / baseline) * 100.0
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.0f}%"


def _max_severity(*levels: str) -> str:
    return max(levels, key=lambda level: _SEVERITY_RANK.get(level, 0))


def _pct_over(current: int, baseline: int) -> float:
    if baseline <= 0:
        return 0.0
    return ((current - baseline) / baseline) * 100.0


def _severity_from_ratio(
    current: int,
    baseline: int,
    *,
    warn_pct: float,
    critical_pct: float,
    warn_absolute: int | None = None,
    critical_absolute: int | None = None,
) -> str:
    levels = [SEVERITY_OK]
    if baseline > 0:
        pct = _pct_over(current, baseline)
        if pct >= critical_pct:
            levels.append(SEVERITY_CRITICAL)
        elif pct >= warn_pct:
            levels.append(SEVERITY_WARN)
    if critical_absolute is not None and current >= critical_absolute:
        levels.append(SEVERITY_CRITICAL)
    elif warn_absolute is not None and current >= warn_absolute:
        levels.append(SEVERITY_WARN)
    return _max_severity(*levels)


def load_compaction_baseline(repo_root: Path, path: Path | None = None) -> dict[str, Any]:
    baseline_path = path or (repo_root / DEFAULT_BASELINE_PATH)
    data = yaml.safe_load(baseline_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"compaction baseline must be a mapping: {baseline_path}")
    return data


def measure_gc0_total(repo_root: Path) -> int:
    total = 0
    for _rel, path in collect_baseline_artifact_paths(repo_root):
        if path.is_file():
            total += line_count_for_path(path)
    return total


def measure_always_on_governance(repo_root: Path) -> tuple[int, int]:
    rows = collect_always_apply_rules(repo_root)
    gov = sum(count for _rel, count, is_gov in rows if is_gov)
    total = sum(count for _rel, count, _is_gov in rows)
    return gov, total


def evaluate_compaction_drift(
    repo_root: Path,
    *,
    baseline_path: Path | None = None,
) -> CompactionReport:
    """Compare current gc0 metrics to compaction-baseline.yaml."""
    baseline = load_compaction_baseline(repo_root, baseline_path)
    thresholds = baseline.get("thresholds") or {}

    gc0_baseline = int(baseline.get("gc0_total_lines", 0))
    gov_baseline = int(baseline.get("always_on_governance_lines", 0))

    gc0_total = measure_gc0_total(repo_root)
    always_on_gov, _always_on_total = measure_always_on_governance(repo_root)

    warn_pct = float(thresholds.get("gc0_total_warn_pct", 15))
    crit_pct = float(thresholds.get("gc0_total_critical_pct", 25))
    gov_warn_lines = int(thresholds.get("always_on_governance_warn_lines", 400))
    gov_crit_lines = int(thresholds.get("always_on_governance_critical_lines", 480))

    artifact_warn_pct = float(thresholds.get("per_artifact_warn_pct", 20))
    artifact_crit_pct = float(thresholds.get("per_artifact_critical_pct", 50))
    artifact_warn_abs = int(thresholds.get("per_artifact_warn_absolute", 600))
    artifact_crit_abs = int(thresholds.get("per_artifact_critical_absolute", 900))

    dup_ref_warn = int(thresholds.get("duplication_reference_warn", 700))
    dup_ref_crit = int(thresholds.get("duplication_reference_critical", 1000))
    dup_rules_warn = int(thresholds.get("duplication_kanban_rules_warn", 600))
    dup_rules_crit = int(thresholds.get("duplication_kanban_rules_critical", 800))

    severity = SEVERITY_OK
    severity = _max_severity(
        severity,
        _severity_from_ratio(gc0_total, gc0_baseline, warn_pct=warn_pct, critical_pct=crit_pct),
    )
    severity = _max_severity(
        severity,
        _severity_from_ratio(
            always_on_gov,
            gov_baseline,
            warn_pct=warn_pct,
            critical_pct=crit_pct,
            warn_absolute=gov_warn_lines,
            critical_absolute=gov_crit_lines,
        ),
    )

    per_baseline: dict[str, int] = dict(baseline.get("per_artifact") or {})
    artifact_signals: list[CompactionSignal] = []
    for rel, path in collect_baseline_artifact_paths(repo_root):
        if not path.is_file():
            continue
        current = line_count_for_path(path)
        file_baseline = per_baseline.get(rel)
        file_severity = SEVERITY_OK
        if file_baseline is not None:
            file_severity = _severity_from_ratio(
                current,
                int(file_baseline),
                warn_pct=artifact_warn_pct,
                critical_pct=artifact_crit_pct,
                warn_absolute=artifact_warn_abs,
                critical_absolute=artifact_crit_abs,
            )
        else:
            file_severity = _severity_from_ratio(
                current,
                0,
                warn_pct=0,
                critical_pct=0,
                warn_absolute=artifact_warn_abs,
                critical_absolute=artifact_crit_abs,
            )
        if file_severity in {SEVERITY_WARN, SEVERITY_CRITICAL}:
            artifact_signals.append(
                CompactionSignal(
                    label=rel,
                    current=current,
                    baseline=int(file_baseline) if file_baseline is not None else None,
                    severity=file_severity,
                )
            )
        severity = _max_severity(severity, file_severity)

    dup_baseline: dict[str, int] = dict(baseline.get("duplication_pairs") or {})
    dup_rows = collect_duplication_pair_counts(repo_root)
    dup_current = {label: count for label, _path, count in dup_rows}
    for label, _keys in (
        ("kanban-markdown reference", ("kanban-markdown reference",)),
        ("kanban-*.mdc (sum)", ("kanban-*.mdc (sum)",)),
    ):
        current = dup_current.get(label, 0)
        base = dup_baseline.get(label)
        warn_abs = dup_ref_warn if "reference" in label else dup_rules_warn
        crit_abs = dup_ref_crit if "reference" in label else dup_rules_crit
        dup_severity = SEVERITY_OK
        if base is not None:
            dup_severity = _severity_from_ratio(
                current,
                int(base),
                warn_pct=artifact_warn_pct,
                critical_pct=artifact_crit_pct,
                warn_absolute=warn_abs,
                critical_absolute=crit_abs,
            )
        else:
            dup_severity = _severity_from_ratio(
                current,
                0,
                warn_pct=0,
                critical_pct=0,
                warn_absolute=warn_abs,
                critical_absolute=crit_abs,
            )
        if dup_severity in {SEVERITY_WARN, SEVERITY_CRITICAL}:
            artifact_signals.append(
                CompactionSignal(
                    label=label,
                    current=current,
                    baseline=int(base) if base is not None else None,
                    severity=dup_severity,
                )
            )
        severity = _max_severity(severity, dup_severity)

    artifact_signals.sort(
        key=lambda sig: (
            -_SEVERITY_RANK.get(sig.severity, 0),
            -(sig.pct_over or 0),
            -sig.current,
        )
    )

    return CompactionReport(
        severity=severity,
        signals=tuple(artifact_signals[:5]),
        gc0_total=gc0_total,
        gc0_baseline=gc0_baseline,
        always_on_governance=always_on_gov,
        always_on_governance_baseline=gov_baseline,
    )


def compaction_drift_lines(
    repo_root: Path,
    *,
    baseline_path: Path | None = None,
    include_severity: bool = True,
    min_severity: str = SEVERITY_WARN,
) -> list[str]:
    """Return drift alert lines when severity >= min_severity (default warn)."""
    from scripts.check_governance_parity import format_drift_line

    report = evaluate_compaction_drift(repo_root, baseline_path=baseline_path)
    if _SEVERITY_RANK.get(report.severity, 0) < _SEVERITY_RANK.get(min_severity, 0):
        return []

    detail = report.summary_line()
    if report.signals:
        outlier_bits = []
        for sig in report.signals[:3]:
            pct = sig.pct_over
            if pct is not None:
                outlier_bits.append(f"{sig.label} +{pct:.0f}%")
            else:
                outlier_bits.append(f"{sig.label} {sig.current}")
        detail = f"{detail}; outliers: {', '.join(outlier_bits)}"
    detail += (
        ". Consider AgentContextBudget epic — "
        "docs/governance/audit-and-compaction.md; "
        "`check_governance_parity.py --compaction`."
    )
    message = f"{PREFIX_COMPACTION} {detail}"
    if include_severity:
        return [format_drift_line(message, severity=report.severity)]
    return [message]


def compute_duplication_aggregates(
    dup_current: dict[str, int],
) -> dict[str, int]:
    """Add classify trio and kanban lifecycle sums to pair counts."""
    aggregates = dict(dup_current)
    aggregates[CLASSIFY_TRIO_SUM_LABEL] = (
        dup_current.get("Classify quickly", 0)
        + dup_current.get("triage §1 Classify", 0)
        + dup_current.get("reference Classify signals", 0)
    )
    aggregates[KANBAN_LIFECYCLE_SUM_LABEL] = dup_current.get(
        "kanban-markdown SKILL (lifecycle)", 0
    ) + dup_current.get("kanban-markdown reference", 0)
    return aggregates


def compare_duplication_count_to_threshold(
    current: int,
    baseline: int | None,
    *,
    warn_pct: float,
    critical_pct: float,
    warn_absolute: int,
    critical_absolute: int,
) -> str:
    """Return severity for one duplication pair vs baseline pct and absolute caps."""
    return _severity_from_ratio(
        current,
        int(baseline) if baseline is not None else 0,
        warn_pct=warn_pct,
        critical_pct=critical_pct,
        warn_absolute=warn_absolute,
        critical_absolute=critical_absolute,
    )


def _duplication_threshold_specs(
    thresholds: dict[str, Any],
) -> tuple[tuple[str, str, str, str], ...]:
    """(label, warn_abs_key, crit_abs_key, spawn_group) for threshold checks."""
    return (
        (
            "kanban-markdown reference",
            "duplication_reference_warn",
            "duplication_reference_critical",
            "kanban",
        ),
        (
            "kanban-*.mdc (sum)",
            "duplication_kanban_rules_warn",
            "duplication_kanban_rules_critical",
            "kanban",
        ),
        (
            CLASSIFY_TRIO_SUM_LABEL,
            "classify_trio_warn",
            "classify_trio_critical",
            "classify",
        ),
        (
            KANBAN_LIFECYCLE_SUM_LABEL,
            "kanban_lifecycle_warn",
            "kanban_lifecycle_critical",
            "kanban_lifecycle",
        ),
    )


def evaluate_duplication_thresholds(
    repo_root: Path,
    *,
    baseline_path: Path | None = None,
) -> tuple[str, tuple[CompactionSignal, ...]]:
    """Compare duplication pairs and aggregates to compaction-baseline.yaml caps."""
    baseline = load_compaction_baseline(repo_root, baseline_path)
    thresholds = baseline.get("thresholds") or {}
    dup_baseline: dict[str, int] = dict(baseline.get("duplication_pairs") or {})

    warn_pct = float(thresholds.get("per_artifact_warn_pct", 20))
    crit_pct = float(thresholds.get("per_artifact_critical_pct", 50))

    dup_rows = collect_duplication_pair_counts(repo_root)
    dup_current = compute_duplication_aggregates(
        {label: count for label, _path, count in dup_rows},
    )

    severity = SEVERITY_OK
    signals: list[CompactionSignal] = []
    for label, warn_key, crit_key, _group in _duplication_threshold_specs(thresholds):
        current = dup_current.get(label, 0)
        base = dup_baseline.get(label)
        pair_severity = compare_duplication_count_to_threshold(
            current,
            base,
            warn_pct=warn_pct,
            critical_pct=crit_pct,
            warn_absolute=int(thresholds.get(warn_key, 0)),
            critical_absolute=int(thresholds.get(crit_key, 0)),
        )
        severity = _max_severity(severity, pair_severity)
        if pair_severity in {SEVERITY_WARN, SEVERITY_CRITICAL}:
            signals.append(
                CompactionSignal(
                    label=label,
                    current=current,
                    baseline=int(base) if base is not None else None,
                    severity=pair_severity,
                )
            )

    signals.sort(
        key=lambda sig: (
            -_SEVERITY_RANK.get(sig.severity, 0),
            -(sig.pct_over or 0),
            -sig.current,
        )
    )
    return severity, tuple(signals)


def duplication_threshold_lines(
    repo_root: Path,
    *,
    baseline_path: Path | None = None,
    include_severity: bool = True,
    min_severity: str = SEVERITY_WARN,
) -> list[str]:
    """Return drift alert lines when duplication pairs exceed post-compaction caps."""
    from scripts.check_governance_parity import PREFIX_DUPLICATION, format_drift_line

    severity, signals = evaluate_duplication_thresholds(
        repo_root,
        baseline_path=baseline_path,
    )
    if _SEVERITY_RANK.get(severity, 0) < _SEVERITY_RANK.get(min_severity, 0):
        return []

    detail_bits = []
    for sig in signals[:4]:
        pct = sig.pct_over
        if pct is not None:
            detail_bits.append(f"{sig.label} +{pct:.0f}% ({sig.current}/{sig.baseline})")
        else:
            detail_bits.append(f"{sig.label} {sig.current} lines")
    detail = "; ".join(detail_bits) if detail_bits else "duplication pair over cap"
    message = (
        f"{PREFIX_DUPLICATION} {detail} — consolidate duplicated governance prose; "
        "Signature: governance-duplication-automation; "
        "run `check_governance_parity.py --duplication-threshold`."
    )
    if include_severity:
        return [format_drift_line(message, severity=severity)]
    return [message]


def format_compaction_advisory_markdown(report: CompactionReport) -> str:
    """Handoff block for agent-self-evaluation SKILL §7."""
    if report.severity not in {SEVERITY_WARN, SEVERITY_CRITICAL}:
        return ""
    signals = report.summary_line()
    return (
        "### Compaction advisory\n"
        f"- **Status:** {report.handoff_status()}\n"
        f"- **Severity:** {report.severity}\n"
        f"- **Signals:** {signals}\n"
        "- **Action:** Review "
        "[audit-and-compaction.md](../../docs/governance/audit-and-compaction.md); "
        "run `python3 scripts/check_governance_parity.py --compaction`; "
        "optional `create_governance_audit_card.py` or work **AgentContextBudget** epic cards\n"
    )
