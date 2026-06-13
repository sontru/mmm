from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
HOST = "0.0.0.0"
DEFAULT_PORT = 8080
DB_PATH = ROOT_DIR / "mmm_server.db"
SESSION_COOKIE = "mmmSession"
SESSION_SECONDS = 60 * 60 * 24 * 30

