from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict 

"""
Read Database URL from .env
"""
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    database_url: str 
    
    # postgreSQL
    postgres_user: str
    postgres_password: str
    postgres_db: str
    
    # minIO
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool
    
    # jwt
    jwt_secret_key: str
    
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
    )

settings = Settings()