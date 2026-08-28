from pydantic_settings import BaseSettings, SettingsConfigDict 

"""
Read Database URL from .env
"""
class Settings(BaseSettings):
    database_url: str 
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()