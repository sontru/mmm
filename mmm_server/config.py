from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
HOST = "0.0.0.0"
DEFAULT_PORT = 8080
DB_PATH = ROOT_DIR / "mmm_server.db"
ADMIN_USER = "api_user"
ADMIN_PASSWORD = "gothic_horror_adventure"
SESSION_COOKIE = "mmmSession"
ADMIN_SESSION_COOKIE = "mmmAdminSession"
SESSION_SECONDS = 60 * 60 * 24 * 30
TESTING = False
