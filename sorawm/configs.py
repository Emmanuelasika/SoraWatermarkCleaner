from pathlib import Path
import os

ROOT = Path(__file__).parent.parent

# Use network volume for models if mounted, otherwise use local resources
# RunPod network volumes are typically mounted at /models
# Environment variable MODELS_DIR defaults to /models for network volume
MODELS_DIR_ENV = os.getenv("MODELS_DIR", "/models")
MODELS_DIR = Path(MODELS_DIR_ENV)

# Ensure models directory exists (will be created on network volume if mounted)
# This allows models to be stored persistently across container restarts
MODELS_DIR.mkdir(parents=True, exist_ok=True)

RESOURCES_DIR = ROOT / "resources"
WATER_MARK_TEMPLATE_IMAGE_PATH = RESOURCES_DIR / "watermark_template.png"

# Store YOLO weights on network volume (will be created if needed)
# The download function checks if file exists before downloading
WATER_MARK_DETECT_YOLO_WEIGHTS = MODELS_DIR / "best.pt"
WATER_MARK_DETECT_YOLO_WEIGHTS_HASH_JSON = MODELS_DIR / "model_version.json"


OUTPUT_DIR = ROOT / "output"

OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


DEFAULT_WATERMARK_REMOVE_MODEL = "lama"

WORKING_DIR = ROOT / "working_dir"
WORKING_DIR.mkdir(exist_ok=True, parents=True)

LOGS_PATH = ROOT / "logs"
LOGS_PATH.mkdir(exist_ok=True, parents=True)

DATA_PATH = ROOT / "data"
DATA_PATH.mkdir(exist_ok=True, parents=True)

SQLITE_PATH = DATA_PATH / "db.sqlite3"
