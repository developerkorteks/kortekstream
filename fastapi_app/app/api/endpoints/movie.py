from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.cache import get_from_cache_or_fetch
from ...schemas.anime import AnimeMovie
from ...services.scraper_factory import ScraperFactory

router = APIRouter()


@router.get("/", response_model=List[AnimeMovie])
async def get_movie_list(page: int = Query(1, ge=1, description="Page number")):
    """
    Get anime movie list.
    
    Args:
        page: Page number (default: 1)
    """
    scraper = ScraperFactory.get_default_scraper()
    if not scraper:
        raise HTTPException(status_code=503, detail="No active scraper available")
    
    cache_key = f"movie_list_page_{page}"
    return get_from_cache_or_fetch(cache_key, scraper.get_movie_list, page)