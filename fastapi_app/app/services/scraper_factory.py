import logging
from typing import Dict, List, Optional, Type

from .scraper import BaseScraper
from .samehadaku_scraper import SamehadakuScraper
from ..core.config import settings

logger = logging.getLogger(__name__)


class ScraperFactory:
    """
    Factory class for creating scraper instances.
    """
    _scrapers: Dict[str, BaseScraper] = {}
    _scraper_classes: Dict[str, Type[BaseScraper]] = {
        "samehadaku": SamehadakuScraper,
        # Tambahkan scraper lain di sini
    }
    
    @classmethod
    def get_scraper(cls, source_name: str) -> Optional[BaseScraper]:
        """
        Get scraper instance for the specified source.
        
        Args:
            source_name: Name of the source
            
        Returns:
            Scraper instance or None if source is not found or not active
        """
        # Check if scraper is already instantiated
        if source_name in cls._scrapers:
            return cls._scrapers[source_name]
        
        # Check if source is in settings
        if source_name not in settings.ANIME_SOURCES:
            logger.error(f"Source {source_name} not found in settings")
            return None
        
        # Check if source is active
        if not settings.ANIME_SOURCES[source_name].get("active", False):
            logger.warning(f"Source {source_name} is not active")
            return None
        
        # Check if scraper class is available
        if source_name not in cls._scraper_classes:
            logger.error(f"Scraper class for source {source_name} not found")
            return None
        
        # Create scraper instance
        try:
            scraper = cls._scraper_classes[source_name]()
            cls._scrapers[source_name] = scraper
            return scraper
        except Exception as e:
            logger.error(f"Error creating scraper for source {source_name}: {e}")
            return None
    
    @classmethod
    def get_active_scrapers(cls) -> List[BaseScraper]:
        """
        Get all active scrapers.
        
        Returns:
            List of active scraper instances
        """
        active_scrapers = []
        
        for source_name, source_config in settings.ANIME_SOURCES.items():
            if source_config.get("active", False):
                scraper = cls.get_scraper(source_name)
                if scraper:
                    active_scrapers.append(scraper)
        
        return active_scrapers
    
    @classmethod
    def get_default_scraper(cls) -> Optional[BaseScraper]:
        """
        Get default scraper (first active scraper).
        
        Returns:
            Default scraper instance or None if no active scraper is found
        """
        active_scrapers = cls.get_active_scrapers()
        return active_scrapers[0] if active_scrapers else None