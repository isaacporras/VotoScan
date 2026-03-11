from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
EXAMPLES_DIR = ASSETS_DIR / "examples"
OUTPUT_DIR = PROJECT_ROOT / "output"

DEPUTIES_JSON = DATA_DIR / "deputies.json"
VOTING_SCREENSHOT = EXAMPLES_DIR / "votacion_1_example.PNG"
ASSEMBLY_TEMPLATE = TEMPLATES_DIR / "asamblea_seats_template.png"
RESULTS_JSON = OUTPUT_DIR / "results.json"
RESULTS_XLSX = OUTPUT_DIR / "results.xlsx"
ASSEMBLY_LABELED = OUTPUT_DIR / "asamblea_seats_labeled.png"
