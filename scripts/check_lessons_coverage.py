#!/usr/bin/env python3
"""Audit Lessons Coverage Metric (C1–C4) for kanban Card Done workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lessons_coverage_lib import (
    CoverageReport,
    build_report,
    format_metric_line,
)
from scripts.resolve_prior_lessons import FEATURES_DIR, find_done_lessons

DEFAULT_THRESHOLD = 75.0


def _pct(score: float | None) -> float | None:
    if score is None:
        return None
    return round(score * 100, 1)


def report_to_dict(report: CoverageReport) -> dict:
    def metric_dict(metric) -> dict:
        return {
            "name": metric.name,
            "numerator": metric.numerator,
            "denominator": metric.denominator,
            "score_pct": _pct(metric.score),
            "detail": metric.detail,
        }

    return {
        "c1": metric_dict(report.c1),
        "c2": metric_dict(report.c2),
        "c3": metric_dict(report.c3),
        "c4": metric_dict(report.c4),
        "composite_pct": _pct(report.composite),
        "per_card_c3": {key: metric_dict(value) for key, value in report.per_card_c3.items()},
    }


def print_report(report: CoverageReport) -> None:
    print("# Lessons Coverage Metric\n")
    for metric in (report.c1, report.c2, report.c3, report.c4):
        print(format_metric_line(metric))
    if report.composite is not None:
        print(f"\nComposite: {report.composite * 100:.1f}% (0.25 × each of C1–C4)")
    else:
        print("\nComposite: N/A")
    for path, metric in report.per_card_c3.items():
        print(f"  {path}: {format_metric_line(metric)}")


def run_audit(
    *,
    mode: str | None = None,
    card: Path | None = None,
    strict: bool = False,
    threshold: float = DEFAULT_THRESHOLD,
    as_json: bool = False,
) -> int:
    report = build_report(
        FEATURES_DIR,
        card=card,
        strict=strict,
        find_lessons=find_done_lessons,
    )

    if mode == "capture":
        report = CoverageReport(
            c1=report.c1,
            c2=report.c2,
            c3=report.c3,
            c4=report.c4,
            composite=report.c1.score,
            per_card_c3={},
        )
    elif mode == "application":
        report = CoverageReport(
            c1=report.c1,
            c2=report.c2,
            c3=report.c3,
            c4=report.c4,
            composite=report.c4.score,
            per_card_c3={},
        )

    if as_json:
        print(json.dumps(report_to_dict(report), indent=2))
    else:
        print_report(report)

    composite_pct = _pct(report.composite)
    if composite_pct is not None and composite_pct < threshold:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--card",
        type=Path,
        help="Compute C3 for one active card (path under .devtool/features/)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="C3: require path/label overlap — epic alone does not match",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Exit 1 when composite %% below this (default {DEFAULT_THRESHOLD})",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    card = args.card
    if card is not None and not card.is_absolute():
        card = REPO_ROOT / card

    return run_audit(
        card=card,
        strict=args.strict,
        threshold=args.threshold,
        as_json=args.json,
    )


if __name__ == "__main__":
    sys.exit(main())
