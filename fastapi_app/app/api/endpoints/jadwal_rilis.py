from typing import Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.cache import get_from_cache_or_fetch
from ...schemas.anime import AnimeSchedule, AnimeScheduleItem
from ...services.scraper_factory import ScraperFactory

router = APIRouter()


@router.get("/", response_model=AnimeSchedule)
async def get_jadwal_rilis_all():
    """
    Get release schedule for all days.
    """
    scraper = ScraperFactory.get_default_scraper()
    if not scraper:
        raise HTTPException(status_code=503, detail="No active scraper available")
    
    cache_key = "jadwal_rilis_all"
    return get_from_cache_or_fetch(cache_key, scraper.get_jadwal_rilis)


@router.get("/{day}", response_model=List[AnimeScheduleItem])
async def get_jadwal_rilis_by_day(day: str):
    """
    Get release schedule for a specific day.
    
    Args:
        day: Day of the week (monday, tuesday, etc.)
    """
    # Validate day
    valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if day.lower() not in valid_days:
        raise HTTPException(status_code=400, detail=f"Invalid day. Valid days are: {', '.join(valid_days)}")
    
    scraper = ScraperFactory.get_default_scraper()
    if not scraper:
        raise HTTPException(status_code=503, detail="No active scraper available")
    
    cache_key = f"jadwal_rilis_{day.lower()}"
    return get_from_cache_or_fetch(cache_key, scraper.get_jadwal_rilis, day.lower())