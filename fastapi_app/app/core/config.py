import os
from typing import Dict, List, Optional, Union, Any
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "KortekStream API"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Anime Source Configuration
    ANIME_SOURCES: Dict[str, Dict[str, Any]] = {
        "samehadaku": {
            "base_url": os.getenv("SAMEHADAKU_BASE_URL", "https://v1.samehadaku.how"),
            "search_url": os.getenv("SAMEHADAKU_SEARCH_URL", "https://samehadaku.now"),
            "api_url": os.getenv("SAMEHADAKU_API_URL", "https://samehadaku.now/wp-json/custom/v1"),
            "active": True,
        },
        # Tambahkan sumber anime lain di sini
    }

    # Cache Configuration
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", 600))  # 10 menit
    CACHE_LONG_TTL: int = int(os.getenv("CACHE_LONG_TTL", 3600))  # 1 jam
    CACHE_VERY_LONG_TTL: int = int(os.getenv("CACHE_VERY_LONG_TTL", 86400))  # 24 jam

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()