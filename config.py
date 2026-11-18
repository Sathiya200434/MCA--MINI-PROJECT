import os
from dotenv import load_dotenv

# Automatically load environment variables from .env in project directory
base_dir = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(base_dir, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
else:
    load_dotenv(override=True)


class Config:
    # ------------------------------------------------------------------ #
    # MySQL 8.0 connection — Database: plant_nursery
    # ------------------------------------------------------------------ #
    MYSQL_USER     = os.environ.get("MYSQL_USER",     "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Root")
    MYSQL_HOST     = os.environ.get("MYSQL_HOST",     "localhost")
    MYSQL_PORT     = os.environ.get("MYSQL_PORT",     "3306")
    MYSQL_DB       = os.environ.get("MYSQL_DB",       "plant_nursery")

    # Primary MySQL 8.0 database connection string
    MYSQL_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    )

    # Use DATABASE_URL if explicitly provided, else default to MySQL URI
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", MYSQL_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask session secret
    SECRET_KEY = os.environ.get("SECRET_KEY", "plant-nursery-production-secure-key-2026")

    # Upload directories (relative paths; app.py resolves to absolute)
    UPLOAD_FOLDER          = os.path.join("static", "images", "plants")
    SERVICE_UPLOAD_FOLDER  = os.path.join("static", "images", "services")
    ALLOWED_EXTENSIONS     = {"png", "jpg", "jpeg", "webp", "gif"}

    # Max upload size: 8 MB
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
