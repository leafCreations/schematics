#!/usr/bin/env bash
# Pre-commit hook: run pytest only for tests related to staged changes.
# Falls back to the full suite when core wiring changes or coverage is too broad.
#
# Skip re-running pytest when tests already passed for the same staged files:
#   scripts/record-pytest-pass.sh   # after a green pytest run
#   SKIP_PRECOMMIT_PYTEST=1 git commit ...   # explicit override (agent use)
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

STAGED_HASH="$(
  git diff --cached --name-only --diff-filter=ACM | LC_ALL=C sort | sha256sum | cut -d' ' -f1
)"

if [[ "${SKIP_PRECOMMIT_PYTEST:-}" == "1" ]]; then
  echo "pre-commit pytest: skipped (SKIP_PRECOMMIT_PYTEST=1)"
  exit 0
fi

STAMP="$ROOT/.pytest-precommit-pass"
if [[ -f "$STAMP" && -n "$STAGED_HASH" ]]; then
  read -r STAMP_HASH STAMP_TIME <"$STAMP" || true
  NOW=$(date +%s)
  MAX_AGE=1800
  if [[ -n "${STAMP_HASH:-}" && -n "${STAMP_TIME:-}" && "$STAMP_HASH" == "$STAGED_HASH" ]]; then
    if ((NOW - STAMP_TIME < MAX_AGE)); then
      echo "pre-commit pytest: skipped (recent pass for same staged files)"
      exit 0
    fi
  fi
fi

if [[ -x "$ROOT/.venv/bin/pytest" ]]; then
  PYTEST="$ROOT/.venv/bin/pytest"
elif [[ -x "$ROOT/venv/bin/pytest" ]]; then
  PYTEST="$ROOT/venv/bin/pytest"
elif command -v pytest >/dev/null 2>&1; then
  PYTEST=pytest
else
  echo "pytest not found. Run: pip install -e \".[dev]\" in the project venv." >&2
  exit 1
fi

_run_pytest() {
  local log
  log="$(mktemp)"
  if ! "$PYTEST" -q "$@" 2>&1 | tee "$log"; then
    "$ROOT/scripts/on_pre_commit_failure.sh" pytest "$log" || true
    rm -f "$log"
    return 1
  fi
  rm -f "$log"
  return 0
}

mapfile -t STAGED < <(git diff --cached --name-only --diff-filter=ACM)

if ((${#STAGED[@]} == 0)); then
  exit 0
fi

declare -A TESTS=()
RUN_FULL=0
CODE_TOUCHED=0
MAX_TARGETED=20

add() {
  for path in "$@"; do
    if [[ -e "$ROOT/$path" ]]; then
      TESTS["$path"]=1
    fi
  done
}

add_glob() {
  shopt -s nullglob
  # Unquoted pattern so bash expands globs (quoted "$ROOT/$1" leaves '*' literal).
  for path in "$ROOT"/$1; do
    TESTS["${path#"$ROOT/"}"]=1
  done
  shopt -u nullglob
}

for file in "${STAGED[@]}"; do
  case "$file" in
    tests/conftest.py | pyproject.toml | setup.py | render_main.py)
      RUN_FULL=1
      ;;

    helpers/context.py | registries/loader.py | helpers/utils.py)
      RUN_FULL=1
      ;;

    helpers/structure_loader.py | helpers/structure_tokens.py)
      CODE_TOUCHED=1
      add tests/test_structure_loader.py tests/test_structure_tokens.py tests/test_ui_document.py
      add tests/test_worldgen_functional_blocks.py
      ;;

    helpers/cells.py)
      CODE_TOUCHED=1
      add tests/test_cells.py
      ;;

    helpers/block_picker.py | helpers/registry_lookup.py | helpers/registry_blocks.py)
      CODE_TOUCHED=1
      add tests/test_block_picker.py tests/test_registry_blocks.py tests/test_registry_phase_b.py
      add tests/test_palette_integrity.py
      ;;

    helpers/grid.py)
      CODE_TOUCHED=1
      add tests/test_grid.py
      ;;

    helpers/grid_cells.py | helpers/grid_placement.py)
      CODE_TOUCHED=1
      add tests/test_grid_cells.py tests/test_grid_placement.py
      ;;

    helpers/layer_rotation.py)
      CODE_TOUCHED=1
      add tests/test_layer_rotation.py
      ;;

    helpers/terrain_tokens.py)
      CODE_TOUCHED=1
      add tests/test_terrain_tokens.py tests/test_sprite_baker_simple.py
      add tests/test_palette_integrity.py tests/test_block_picker.py
      ;;

    helpers/fence_adjacency.py)
      CODE_TOUCHED=1
      add tests/test_fence_adjacency.py tests/test_utils_schematics_fence.py
      add tests/test_wall_blockstates.py tests/test_utils_schematics_wall.py
      add_glob "tests/test_sprite_baker_fence.py"
      add_glob "tests/test_sprite_baker_wall.py"
      ;;

    helpers/wall_blockstates.py)
      CODE_TOUCHED=1
      add tests/test_wall_blockstates.py tests/test_utils_schematics_wall.py
      add_glob "tests/test_sprite_baker_wall.py"
      add tests/test_fence_adjacency.py tests/test_palette_integrity.py
      ;;

    helpers/lantern_placement.py)
      CODE_TOUCHED=1
      add tests/test_lantern_placement.py tests/test_sprite_baker_lantern.py
      ;;

    helpers/paths.py | helpers/layers.py | helpers/layer_management.py)
      CODE_TOUCHED=1
      add tests/test_paths.py tests/test_layers.py tests/test_layer_management.py
      add tests/test_worldgen_functional_blocks.py
      ;;

    helpers/materials.py | helpers/collect_material_tokens.py)
      CODE_TOUCHED=1
      add tests/test_materials.py tests/test_collect_material_tokens.py
      ;;

    helpers/landscape_utils.py | helpers/path_geometry.py | helpers/path_strip.py)
      CODE_TOUCHED=1
      add tests/test_landscape_utils.py tests/test_path_geometry.py tests/test_path_strip.py
      add tests/test_path_lighting.py tests/test_site_display_lighting.py
      ;;

    helpers/utils_schematics.py | helpers/facade_projection.py)
      CODE_TOUCHED=1
      add tests/test_utils_schematics.py tests/test_facade_projection.py
      add_glob "tests/test_utils_schematics_*.py"
      ;;

    helpers/sprite_baker/*)
      CODE_TOUCHED=1
      add_glob "tests/test_sprite_baker_*.py"
      add tests/test_sprite_baker_cache.py
      ;;

    helpers/block_catalog.py)
      CODE_TOUCHED=1
      add tests/test_block_catalog.py tests/test_block_picker.py
      ;;

    helpers/pipeline.py | helpers/paths.py | helpers/render_image.py | helpers/fonts.py)
      CODE_TOUCHED=1
      add tests/test_paths.py tests/test_pipeline.py tests/test_fonts.py
      ;;

    helpers/site_ground.py | helpers/structure_metadata.py)
      CODE_TOUCHED=1
      add tests/test_ui_document.py tests/test_site_cells.py tests/test_structure_metadata.py
      ;;

    helpers/*)
      CODE_TOUCHED=1
      add tests/test_utils.py
      ;;

    registries/validate.py | registries/palettes/* | registries/behaviors/* | registries/generated/*)
      CODE_TOUCHED=1
      add tests/test_palette_integrity.py tests/test_registry_reload.py tests/test_registry_phase_b.py
      add tests/test_block_picker.py
      ;;

    renderers/worldgen.py | helpers/worldgen_*.py)
      CODE_TOUCHED=1
      add tests/test_worldgen_chest.py tests/test_worldgen_tokens.py tests/test_worldgen_site.py
      add tests/test_worldgen_bed.py tests/test_worldgen_region_patch.py tests/test_worldgen_functional_blocks.py
      add tests/test_lantern_placement.py tests/test_fence_adjacency.py
      ;;

    renderers/*)
      CODE_TOUCHED=1
      add tests/test_facade_projection.py tests/test_layers.py tests/test_pipeline.py
      add tests/test_render_panel.py
      ;;

    ui/document.py | ui/editor_history.py | ui/editor_materials.py | ui/app_settings.py | ui/editor_prefs.py)
      CODE_TOUCHED=1
      add tests/test_ui_document.py tests/test_editor_history.py
      ;;

    ui/texture_cache.py | ui/materials_icons.py | ui/site_cells.py)
      CODE_TOUCHED=1
      add tests/test_texture_cache.py tests/test_site_cells.py
      ;;

    ui/toolbar_icons.py | ui/icon_theme.py | ui/main_window.py | ui/widgets/layer_list_panel.py | ui/widgets/layer_tools_panel.py | ui/widgets/structure_properties_panel.py | ui/widgets/* | ui/platform.py)
      CODE_TOUCHED=1
      add_glob "tests/test_ui_*.py"
      add tests/test_main_window.py tests/test_render_panel.py tests/test_texture_cache.py
      add tests/test_structure_metadata.py
      ;;

    ui/*)
      CODE_TOUCHED=1
      add_glob "tests/test_ui_*.py"
      add tests/test_main_window.py
      ;;

    structures/*)
      CODE_TOUCHED=1
      add tests/test_structure_loader.py tests/test_ui_document.py
      add tests/test_worldgen_functional_blocks.py tests/test_worldgen_chest.py
      ;;

    tests/test_*.py)
      CODE_TOUCHED=1
      add "$file"
      ;;

    scripts/migrate_structure_to_yaml.py)
      CODE_TOUCHED=1
      add tests/test_structure_loader.py
      ;;

    docs/feature-areas.yaml)
      CODE_TOUCHED=1
      add tests/test_resolve_feature_areas.py tests/test_check_governance_parity.py
      ;;

    scripts/check_governance_parity.py | scripts/resolve_feature_areas.py)
      CODE_TOUCHED=1
      add tests/test_resolve_feature_areas.py tests/test_check_governance_parity.py
      ;;

    scripts/bake_sprites.py | scripts/generate_catalog.py | scripts/prune_minecraft_assets.py | scripts/migrate_project_assets.py | scripts/dedupe_minecraft_assets.py)
      CODE_TOUCHED=1
      add_glob "tests/test_sprite_baker_*.py"
      add tests/test_block_catalog.py
      add tests/test_minecraft_assets.py
      ;;

    *.py | *.pyi)
      CODE_TOUCHED=1
      ;;
  esac
done

if ((RUN_FULL)); then
  echo "pre-commit pytest: full suite (core or global change detected)"
  _run_pytest || exit 1
  exit 0
fi

if ((${#TESTS[@]} > MAX_TARGETED)); then
  echo "pre-commit pytest: full suite (${#TESTS[@]} targeted files > ${MAX_TARGETED})"
  _run_pytest || exit 1
  exit 0
fi

if ((${#TESTS[@]} == 0)); then
  if ((CODE_TOUCHED)); then
    echo "pre-commit pytest: full suite (unmapped code changes)"
    _run_pytest || exit 1
    exit 0
  fi

  echo "pre-commit pytest: skipped (no mapped code changes)"
  exit 0
fi

mapfile -t TEST_LIST < <(printf '%s\n' "${!TESTS[@]}" | sort)

echo "pre-commit pytest: ${#TEST_LIST[@]} file(s) — ${TEST_LIST[*]}"
_run_pytest "${TEST_LIST[@]}" || exit 1
