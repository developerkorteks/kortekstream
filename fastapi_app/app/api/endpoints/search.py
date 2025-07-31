from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.cache import get_from_cache_or_fetch
from ...schemas.anime import AnimeSearch
from ...services.scraper_factory import ScraperFactory

router = APIRouter()


@router.get("/", response_model=List[AnimeSearch])
async def search_anime(query: str = Query(..., description="Search query")):
    """
    Search for anime.
    
    Args:
        query: Search query
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty")
    
    scraper = ScraperFactory.get_default_scraper()
    if not scraper:
        raise HTTPException(status_code=503, detail="No active scraper available")
    
    cache_key = f"search_{query}"
    result = get_from_cache_or_fetch(cache_key, scraper.search, query)
    
    return result or []