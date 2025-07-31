from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.cache import get_from_cache_or_fetch
from ...schemas.anime import EpisodeDetail
from ...services.scraper_factory import ScraperFactory

router = APIRouter()


@router.get("/", response_model=EpisodeDetail)
async def get_episode_detail(episode_url: str = Query(..., description="Episode URL")):
    """
    Get episode details.
    
    Args:
        episode_url: Episode URL
    """
    scraper = ScraperFactory.get_default_scraper()
    if not scraper:
        raise HTTPException(status_code=503, detail="No active scraper available")
    
    cache_key = f"episode_detail_{episode_url}"
    result = get_from_cache_or_fetch(cache_key, scraper.get_episode_details, episode_url)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Episode with URL '{episode_url}' not found")
    
    return result