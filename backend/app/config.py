import os

def _normalize_database_url(url: str) -> str:
    # Render/Heroku sometimes provide postgres:// which SQLAlchemy expects as postgresql://
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

class Config:
    # Base directory of the backend (one level above this `app` package)
    BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    INSTANCE_DIR = os.path.join(BACKEND_DIR, 'instance')
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    _default_sqlite_path = os.path.join(INSTANCE_DIR, 'fliptrybe.db').replace('\\', '/')
    _db_url = os.getenv("DATABASE_URL", f"sqlite:///{_default_sqlite_path}")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(_db_url)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS: comma-separated origins for web builds (e.g. https://yourapp.web.app,https://yourdomain.com)
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
