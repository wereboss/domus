from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

class Settings(BaseSettings):
    APP_NAME: str = "Domus - Your Home, Organised"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Storage & DB Paths (Option A: Strict Dual SQLite Isolation)
    LOGISTICS_DB_PATH: Path = DATA_DIR / "logistics.db"
    FINANCE_DB_PATH: Path = DATA_DIR / "finance.db"
    
    # App Server Port
    PORT: int = 9035

    # Localization defaults
    CURRENCY_SYMBOL: str = "$"
    TIME_FORMAT: str = "24h"
    DEFAULT_TIMEZONE: str = "UTC"
    
    # Auth & Security
    SECRET_KEY: str = "domus-insecure-dev-secret-change-in-production-32-chars-minimum"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 90  # Long-lived persistent device session

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
