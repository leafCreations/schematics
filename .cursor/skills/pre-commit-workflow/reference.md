# Pre-Commit Workflow — Reference

Path→test selection and hook scope: [targeted-testing/reference.md](../targeted-testing/reference.md). Hook script source of truth: `scripts/pre-commit-pytest.sh`.

Row schema (phase 1): [agent-self-evaluation/SKILL.md](../agent-self-evaluation/SKILL.md) §6f.

## Failure patterns

Area-specific hook and pytest mistakes. Promote from **`commit-issue`** cards on review when reusable — [kanban-commit-issue-cards.mdc](../../rules/kanban-commit-issue-cards.mdc).

| Signature | Trigger snippet | Fix pattern | Skill | Rule |
| --------- | --------------- | ----------- | ----- | ---- |
| `precommit-stash-old-hooks` | commit failed, no `commit-issue` card; unstaged `scripts/pre-commit-*.sh` or `on_pre_commit_failure.sh` | Pre-commit stashes unstaged changes — old hook scripts run without capture. Stage all hook infra (`.pre-commit-config.yaml`, `scripts/pre-commit-*.sh`, `scripts/on_pre_commit_failure.sh`, `scripts/create_commit_issue_card.py`); run `pre-commit install` after wiring changes | pre-commit-workflow | testing.mdc |
| `precommit-pytest-scope-mismatch` | narrow `pytest` green, commit fails on pytest hook | Re-run `scripts/pre-commit-pytest.sh` on staged paths — match hook scope, not a hand-picked file | pre-commit-workflow | testing.mdc |
| `precommit-ruff-dirty-after-fix` | ruff hook passed, commit still blocked / dirty tree | Hook re-staged fixed files — `git status`, `git add` any remaining, commit again | pre-commit-workflow | — |
| `precommit-ruff-staged-venv` | ruff mass F405/UP031/SIM* in `site-packages` or `.tmp-venv/`; thousands of errors | Unstage venv; add `.tmp-venv/` to `.gitignore`; filter `.venv/`, `.tmp-venv/`, `site-packages/` in `pre-commit-ruff.sh`; `extend-exclude` in `pyproject.toml` | pre-commit-workflow | testing.mdc |
| `precommit-palette-top-texture` | `top texture … not found` in validate-palettes | Add texture under assets + bake, or skip top check only when behavior has no `render.textures.top` (`registries/validate.py`) | pre-commit-workflow | — |
| `precommit-no-card-skip-env` | expected card missing; `SKIP_COMMIT_ISSUE_CARD=1` | Intentional disable for CI/retries — do not expect a card; use `git commit` without skip for local capture | pre-commit-workflow | — |
| `precommit-mainwindow-__new__-test` | `AttributeError: '_preview_panel'` in `test_main_window` using `MainWindow.__new__` | Guard optional widgets in `_clear_preview_session` (`getattr(self, "_preview_panel", None)`) or stub panel on test instance | pre-commit-workflow | testing.mdc |

**Lookup:** on failure signals, [agent-triage/SKILL.md](../agent-triage/SKILL.md) §1b → grep **Signature** or **Trigger snippet** here before re-diagnosing. Cross-cutting patterns: [agent-self-evaluation/reference.md](../agent-self-evaluation/reference.md) § Common failure patterns.

**Promotion:** on `commit-issue` **review**, agent asks “reusable pattern?” → if yes, add a row here (and cite **Signature** in `testing.mdc` when a hook-level constraint applies).
