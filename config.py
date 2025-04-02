from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    # Notion settings
    NOTION_TOKEN: str
    NOTION_DATABASE_ID: str
    
    # API settings
    POKEMON_TCG_API_KEY: Optional[str] = None
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings() 