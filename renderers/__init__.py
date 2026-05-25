from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ASSET_FOLDER = BASE_DIR / "assets"
OUTPUT_SCHEMATICS_FOLDER = BASE_DIR / "output/schematics"
OUTPUT_WORLDS_FOLDER = BASE_DIR / "output/worlds"
STRUCTURES_FOLDER = BASE_DIR / "structures"
TEMPLATE_FOLDER = BASE_DIR / "template"

MAX_PANELS_PER_ROW = 3
MAX_PANEL_ROWS_PER_IMAGE = 3