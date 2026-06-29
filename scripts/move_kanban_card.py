#!/usr/bin/env python3
"""Idempotent kanban card resolve + move across features / done / archived buckets.

Signature: ``kanban-card-move-resolver``. Bounded O(3) bucket scan — no ``find`` or broad glob.

Example::

    python3 scripts/move_kanban_card.py --id my-card-2026-06-29 --to done
    python3 scripts/move_kanban_card.py my-card-stem --to archived --set-done
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FEATURES_DIR = REPO_ROOT / ".devtool" / "features"
_TARGET_BUCKETS = frozenset({"done", "archived"})

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.resolve_prior_lessons import _parse_frontmatter  # noqa: E402


@dataclass
class ResolvedCard:
    """A kanban card located under active, done, or archived."""

    path: Path
    bucket: str
    card_id: str
    stem: str


def _card_dirs(features_dir: Path) -> list[tuple[Path, str]]:
    return [
        (features_dir, "active"),
        (features_dir / "done", "done"),
        (features_dir / "archived", "archived"),
    ]


def _bucket_dir(features_dir: Path, bucket: str) -> Path:
    if bucket == "active":
        return features_dir
    return features_dir / bucket


def rel_repo_path(path: Path) -> str:
    """Repo-relative path string for agent capture."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _matches_card(path: Path, *, stem: str | None, card_id: str | None) -> bool:
    if not path.is_file() or path.suffix != ".md":
        return False
    if stem is not None and path.stem != stem:
        return False
    text = path.read_text(encoding="utf-8")
    meta = _parse_frontmatter(text)
    return card_id is None or str(meta.get("id") or "") == card_id


def resolve_kanban_card(
    *,
    stem: str | None = None,
    card_id: str | None = None,
    features_dir: Path | None = None,
) -> ResolvedCard | None:
    """Find card by filename stem and/or frontmatter ``id`` (active → done → archived)."""
    if stem is None and card_id is None:
        return None
    root = features_dir or DEFAULT_FEATURES_DIR
    for directory, bucket in _card_dirs(root):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            if not _matches_card(path, stem=stem, card_id=card_id):
                continue
            text = path.read_text(encoding="utf-8")
            meta = _parse_frontmatter(text)
            resolved_id = str(meta.get("id") or path.stem)
            return ResolvedCard(
                path=path,
                bucket=bucket,
                card_id=resolved_id,
                stem=path.stem,
            )
    return None


def _target_path(features_dir: Path, stem: str, target: str) -> Path:
    return _bucket_dir(features_dir, target) / f"{stem}.md"


def _apply_set_done(path: Path, *, when: datetime | None = None) -> None:
    ts = when or datetime.now(UTC)
    iso = ts.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return
    end = text.find("\n---", 3)
    if end == -1:
        return
    front = text[3:end]
    body = text[end + 4 :]
    lines = front.splitlines()
    out: list[str] = []
    seen_status = seen_completed = seen_modified = False
    for line in lines:
        if line.startswith("status:"):
            out.append('status: "done"')
            seen_status = True
        elif line.startswith("completedAt:"):
            out.append(f'completedAt: "{iso}"')
            seen_completed = True
        elif line.startswith("modified:"):
            out.append(f'modified: "{iso}"')
            seen_modified = True
        else:
            out.append(line)
    if not seen_status:
        out.append('status: "done"')
    if not seen_completed:
        out.append(f'completedAt: "{iso}"')
    if not seen_modified:
        out.append(f'modified: "{iso}"')
    path.write_text("---\n" + "\n".join(out) + "\n---" + body, encoding="utf-8")


def move_kanban_card(
    resolved: ResolvedCard,
    *,
    target: str,
    features_dir: Path | None = None,
    set_done: bool = False,
) -> Path:
    """Move card to ``done`` or ``archived``; idempotent when already in target bucket."""
    if target not in _TARGET_BUCKETS:
        raise ValueError(f"invalid target bucket: {target}")
    root = features_dir or DEFAULT_FEATURES_DIR
    dest = _target_path(root, resolved.stem, target)
    if resolved.bucket == target and resolved.path.resolve() == dest.resolve():
        if set_done:
            _apply_set_done(resolved.path)
        return resolved.path
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.resolve() != resolved.path.resolve():
        raise FileExistsError(f"target already exists: {dest}")
    if resolved.path.resolve() != dest.resolve():
        shutil.move(str(resolved.path), str(dest))
    if set_done:
        _apply_set_done(dest)
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve and move kanban cards idempotently (kanban-card-move-resolver).",
    )
    parser.add_argument("stem", nargs="?", help="Card filename stem (without .md)")
    parser.add_argument("--id", dest="card_id", help="Frontmatter id value")
    parser.add_argument("--to", required=True, choices=sorted(_TARGET_BUCKETS))
    parser.add_argument(
        "--set-done",
        action="store_true",
        help="Set status done, completedAt, and modified ISO timestamps",
    )
    parser.add_argument(
        "--features-dir",
        type=Path,
        default=None,
        help="Override features root (tests only)",
    )
    args = parser.parse_args(argv)

    stem = args.stem
    if stem and stem.endswith(".md"):
        stem = Path(stem).stem

    if not stem and not args.card_id:
        print("move_kanban_card: pass stem or --id", file=sys.stderr)
        return 1

    features_dir = args.features_dir
    resolved = resolve_kanban_card(stem=stem, card_id=args.card_id, features_dir=features_dir)
    if resolved is None:
        print("move_kanban_card: card not found", file=sys.stderr)
        return 1

    try:
        final = move_kanban_card(
            resolved,
            target=args.to,
            features_dir=features_dir,
            set_done=args.set_done,
        )
    except FileExistsError as exc:
        print(f"move_kanban_card: {exc}", file=sys.stderr)
        return 1

    print(rel_repo_path(final))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
