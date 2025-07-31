from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.cache import get_from_cache_or_fetch
from ...schemas.anime import AnimeDetail
from ...services.scraper_factory import ScraperFactory

router = APIRouter()


@router.get("/", response_model=AnimeDetail)
async def get_anime_detail(anime_slug: str = Query(..., description="Anime slug")):
    """
    Get anime details.
    
    Args:
        anime_slug: Anime slug
    """
    scraper = ScraperFactory.get_default_scraper()
    if not scraper:
        raise HTTPException(status_code=503, detail="No active scraper available")
    
    cache_key = f"anime_detail_{anime_slug}"
    result = get_from_cache_or_fetch(cache_key, scraper.get_anime_details, anime_slug)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Anime with slug '{anime_slug}' not found")
    
    return result