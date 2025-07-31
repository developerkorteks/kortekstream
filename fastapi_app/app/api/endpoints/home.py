from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.cache import get_from_cache_or_fetch
from ...schemas.anime import HomeData
from ...services.scraper_factory import ScraperFactory

router = APIRouter()


@router.get("/", response_model=HomeData)
async def get_home_data():
    """
    Get home page data.
    """
    scraper = ScraperFactory.get_default_scraper()
    if not scraper:
        raise HTTPException(status_code=503, detail="No active scraper available")
    
    cache_key = "home_data"
    result = get_from_cache_or_fetch(cache_key, scraper.get_home_data)
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to get home page data")
    
    return result