#!/usr/bin/env python3
"""Sync AGENTS.md Area → skills & rules table from docs/feature-areas.yaml.

Signature: governance-area-schema-agents-table-sync (gs4).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_governance_parity import (  # noqa: E402
    PREFIX_REGISTRY,
    AreaSchemaEntry,
    _rule_file_from_entry,
    load_area_schema_entries,
)

AGENTS_AREA_HEADING = "## Area → skills & rules"
TABLE_END_MARKER = "Path→test map:"
PREFIX_REGISTRY_AREA = f"{PREFIX_REGISTRY} AGENTS area table"

# Narrative Area column substrings → yaml area name (schema keys unchanged).
AREA_LABEL_ALIASES: dict[str, tuple[str, ...]] = {
    "Agent Workflow": ("agent / routing", "agent workflow"),
    "Feature Area Registry": ("kanban /", "feature area registry"),
    "Properties Panel": ("properties panel", "ui panels"),
    "Render Preview": ("render preview",),
    "Palette Registry": ("palette registry", "registry / palettes"),
}

_SKILL_PATH_RE = re.compile(r"\.cursor/skills/([^/)\s]+)")
_RULE_PATH_RE = re.compile(r"\.cursor/rules/([a-z0-9_-]+\.mdc)")


@dataclass(frozen=True)
class AgentsAreaRow:
    area_label: str
    skills_md: str
    rules_md: str


@dataclass
class AgentsAreaTable:
    before_table: str
    table_header: str
    rows: list[AgentsAreaRow]
    after_table: str


def _load_area_paths(feature_areas_text: str, area_name: str) -> tuple[str, ...]:
    if yaml is None:
        return ()
    data = yaml.safe_load(feature_areas_text)
    entry = data.get("areas", {}).get(area_name, {})
    if not isinstance(entry, dict):
        return ()
    raw_paths = entry.get("paths", []) or []
    return tuple(str(path).strip() for path in raw_paths if str(path).strip())


def row_matches_area(area_label: str, entry: AreaSchemaEntry) -> bool:
    lower = area_label.lower()
    needles = [entry.name.lower()]
    if entry.lesson_routing_row:
        needles.append(entry.lesson_routing_row.lower())
    needles.extend(alias.lower() for alias in AREA_LABEL_ALIASES.get(entry.name, ()))
    return any(needle in lower for needle in needles)


def _skill_stems_from_paths(paths: tuple[str, ...]) -> list[str]:
    stems: list[str] = []
    for path in paths:
        if path.endswith("/SKILL.md"):
            stem = Path(path).parent.name
        elif "/.cursor/skills/" in path or path.startswith(".cursor/skills/"):
            match = _SKILL_PATH_RE.search(path)
            stem = match.group(1) if match else Path(path.rstrip("/")).name
        else:
            continue
        if stem and stem not in stems:
            stems.append(stem)
    return stems


def build_skills_column(
    entry: AreaSchemaEntry,
    paths: tuple[str, ...],
) -> str:
    stems: list[str] = [entry.agents_skill]
    for stem in _skill_stems_from_paths(paths):
        if stem not in stems:
            stems.append(stem)
    links: list[str] = []
    for stem in stems:
        skill_path = f".cursor/skills/{stem}/SKILL.md"
        links.append(f"[{stem}]({skill_path})")
    if "kanban-markdown" in stems:
        ref = ".cursor/skills/kanban-markdown/reference.md"
        links.append(f"[reference]({ref})")
    return ", ".join(links)


def build_rules_column(rules: tuple[str, ...]) -> str:
    if not rules:
        return "—"
    links: list[str] = []
    seen: set[str] = set()
    for rule_entry in rules:
        rule_file = _rule_file_from_entry(rule_entry)
        stem = rule_file.removesuffix(".mdc")
        if stem in seen:
            continue
        seen.add(stem)
        links.append(f"[{stem}](.cursor/rules/{rule_file})")
    return ", ".join(links)


def _parse_table_row(line: str) -> AgentsAreaRow | None:
    if not line.strip().startswith("|"):
        return None
    if re.match(r"^\|\s*[-:]+", line):
        return None
    cells = [cell.strip() for cell in line.split("|")[1:-1]]
    if len(cells) < 3:
        return None
    head = cells[0].lower().strip("*")
    if head in {"area", "label"}:
        return None
    return AgentsAreaRow(area_label=cells[0], skills_md=cells[1], rules_md=cells[2])


def parse_agents_area_table(agents_text: str) -> AgentsAreaTable | None:
    idx = agents_text.find(AGENTS_AREA_HEADING)
    if idx < 0:
        return None
    after_heading = agents_text[idx + len(AGENTS_AREA_HEADING) :]
    table_start = after_heading.find("| Area |")
    if table_start < 0:
        return None
    before_table = agents_text[: idx + len(AGENTS_AREA_HEADING)] + after_heading[:table_start]
    table_block = after_heading[table_start:]
    end_idx = table_block.find(TABLE_END_MARKER)
    if end_idx < 0:
        end_rel = table_block.find("\n## ")
        table_text = table_block if end_rel < 0 else table_block[:end_rel]
        after_table = table_block[len(table_text) :]
    else:
        table_text = table_block[:end_idx]
        after_table = table_block[end_idx:]

    lines = table_text.splitlines()
    header_lines: list[str] = []
    rows: list[AgentsAreaRow] = []
    in_header = True
    for line in lines:
        if in_header:
            header_lines.append(line)
            if re.match(r"^\|\s*[-:]+", line):
                in_header = False
            continue
        parsed = _parse_table_row(line)
        if parsed:
            rows.append(parsed)
    return AgentsAreaTable(
        before_table=before_table.rstrip() + "\n\n",
        table_header="\n".join(header_lines) + "\n",
        rows=rows,
        after_table=after_table.lstrip("\n"),
    )


def _extract_skill_stems(skills_md: str) -> set[str]:
    stems: set[str] = set()
    for match in _SKILL_PATH_RE.finditer(skills_md):
        stems.add(match.group(1))
    return stems


def _extract_rule_files(rules_md: str) -> set[str]:
    if rules_md.strip() in {"—", "-", ""}:
        return set()
    return set(_RULE_PATH_RE.findall(rules_md))


def expected_row_for_entry(
    entry: AreaSchemaEntry,
    feature_areas_text: str,
) -> AgentsAreaRow:
    paths = _load_area_paths(feature_areas_text, entry.name)
    default_label = AREA_LABEL_ALIASES.get(entry.name, (entry.name,))[0]
    if entry.name == "Agent Workflow":
        default_label = "Agent / routing / self-eval"
    elif entry.name == "Feature Area Registry":
        default_label = "Kanban / `.devtool/features/`"
    elif entry.name == "Properties Panel":
        default_label = "UI panels / dialogs"
    elif entry.name == "Palette Registry":
        default_label = "Registry / palettes"
    elif entry.name == "Render Preview":
        default_label = "Render Preview"
    return AgentsAreaRow(
        area_label=default_label.title() if default_label == entry.name else default_label,
        skills_md=build_skills_column(entry, paths),
        rules_md=build_rules_column(entry.agents_rules),
    )


def check_agents_area_table_parity(
    agents_text: str,
    schema_entries: list[AreaSchemaEntry],
    feature_areas_text: str,
) -> list[str]:
    table = parse_agents_area_table(agents_text)
    issues: list[str] = []
    if table is None:
        issues.append(f"{PREFIX_REGISTRY_AREA} — missing `{AGENTS_AREA_HEADING}` table")
        return issues

    matched_indices: set[int] = set()
    for entry in schema_entries:
        expected = expected_row_for_entry(entry, feature_areas_text)
        exp_skills = _extract_skill_stems(expected.skills_md)
        exp_rules = _extract_rule_files(expected.rules_md)

        row_idx = None
        for idx, row in enumerate(table.rows):
            if row_matches_area(row.area_label, entry):
                row_idx = idx
                break

        if row_idx is None:
            issues.append(
                f"{PREFIX_REGISTRY_AREA} — no row for yaml area **{entry.name}** "
                f"(`agents_skill`: `{entry.agents_skill}`)"
            )
            continue

        matched_indices.add(row_idx)
        row = table.rows[row_idx]
        act_skills = _extract_skill_stems(row.skills_md)
        act_rules = _extract_rule_files(row.rules_md)

        missing_skills = exp_skills - act_skills
        stale_skills = act_skills - exp_skills
        if missing_skills:
            issues.append(
                f"{PREFIX_REGISTRY_AREA} row `{row.area_label}` missing skills "
                f"{sorted(missing_skills)} (yaml **{entry.name}**)"
            )
        if stale_skills:
            issues.append(
                f"{PREFIX_REGISTRY_AREA} row `{row.area_label}` stale skills "
                f"{sorted(stale_skills)} (yaml **{entry.name}**)"
            )

        missing_rules = exp_rules - act_rules
        stale_rules = act_rules - exp_rules
        if missing_rules:
            issues.append(
                f"{PREFIX_REGISTRY_AREA} row `{row.area_label}` missing rules "
                f"{sorted(missing_rules)} (yaml **{entry.name}**)"
            )
        if stale_rules:
            issues.append(
                f"{PREFIX_REGISTRY_AREA} row `{row.area_label}` stale rules "
                f"{sorted(stale_rules)} (yaml **{entry.name}**)"
            )

    return issues


def sync_agents_area_table_text(
    agents_text: str,
    schema_entries: list[AreaSchemaEntry],
    feature_areas_text: str,
) -> str:
    table = parse_agents_area_table(agents_text)
    if table is None:
        raise ValueError(f"Missing {AGENTS_AREA_HEADING} table in AGENTS.md")

    updated_rows: list[AgentsAreaRow] = []
    consumed: set[str] = set()

    for row in table.rows:
        matched_entry = None
        for entry in schema_entries:
            if entry.name in consumed:
                continue
            if row_matches_area(row.area_label, entry):
                matched_entry = entry
                break
        if matched_entry:
            consumed.add(matched_entry.name)
            expected = expected_row_for_entry(matched_entry, feature_areas_text)
            updated_rows.append(
                AgentsAreaRow(
                    area_label=row.area_label,
                    skills_md=expected.skills_md,
                    rules_md=expected.rules_md,
                )
            )
        else:
            updated_rows.append(row)

    for entry in schema_entries:
        if entry.name in consumed:
            continue
        expected = expected_row_for_entry(entry, feature_areas_text)
        updated_rows.append(expected)

    body_rows = "\n".join(
        f"| {row.area_label} | {row.skills_md} | {row.rules_md} |" for row in updated_rows
    )
    intro = table.before_table
    intro = intro.replace(
        "This table stays narrative until a follow-up epic syncs or generates rows from yaml "
        "(Signature: `governance-area-schema-defer-agents-table`).",
        "Yaml-synced rows (`agents_skill` areas) — Signature: "
        "`governance-area-schema-agents-table-sync`; "
        "`python3 scripts/sync_agents_area_table.py --check`.",
    )
    intro = intro.replace(
        "**Narrative routing table** — **gs0–gs3 complete** (`GovernanceAreaSchema` epic).",
        "**Yaml-synced routing table** — **gs4 complete** (`AgentsTableSync` epic).",
    )
    return intro + table.table_header + body_rows + "\n\n" + table.after_table


def write_agents_area_table(
    repo_root: Path,
    *,
    dry_run: bool = False,
) -> tuple[str, list[str]]:
    agents_path = repo_root / "AGENTS.md"
    yaml_path = repo_root / "docs/feature-areas.yaml"
    agents_text = agents_path.read_text(encoding="utf-8")
    feature_areas_text = yaml_path.read_text(encoding="utf-8")
    entries = load_area_schema_entries(feature_areas_text)
    issues = check_agents_area_table_parity(agents_text, entries, feature_areas_text)
    synced = sync_agents_area_table_text(agents_text, entries, feature_areas_text)
    if not dry_run and synced != agents_text:
        agents_path.write_text(synced, encoding="utf-8")
    return synced, issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when AGENTS area table drifts from yaml",
    )
    parser.add_argument(
        "--write",
        "--fix",
        dest="write",
        action="store_true",
        help="Update AGENTS.md area table section from yaml",
    )
    args = parser.parse_args(argv)

    if yaml is None:
        print("sync_agents_area_table: PyYAML not installed", file=sys.stderr)
        return 2

    root = args.repo_root
    agents_path = root / "AGENTS.md"
    yaml_path = root / "docs/feature-areas.yaml"
    if not agents_path.is_file() or not yaml_path.is_file():
        print("sync_agents_area_table: missing AGENTS.md or feature-areas.yaml", file=sys.stderr)
        return 2

    agents_text = agents_path.read_text(encoding="utf-8")
    feature_areas_text = yaml_path.read_text(encoding="utf-8")
    entries = load_area_schema_entries(feature_areas_text)
    issues = check_agents_area_table_parity(agents_text, entries, feature_areas_text)

    if args.write:
        synced, _ = write_agents_area_table(root, dry_run=False)
        agents_text = synced
        issues = check_agents_area_table_parity(agents_text, entries, feature_areas_text)

    if issues:
        for line in issues:
            print(line)
        if args.check or args.write:
            return 1
        return 0

    if args.write:
        print("AGENTS.md area table synced from feature-areas.yaml")
    elif args.check:
        print("AGENTS area table matches feature-areas.yaml")
    else:
        parser.print_help()
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
