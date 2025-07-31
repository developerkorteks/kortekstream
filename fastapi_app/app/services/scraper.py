from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import requests
from bs4 import BeautifulSoup
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Base class for all scrapers.
    """
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.source_config = self._get_source_config()
        self.base_url = self.source_config.get("base_url", "")
        self.search_url = self.source_config.get("search_url", "")
        self.api_url = self.source_config.get("api_url", "")
        self.active = self.source_config.get("active", False)
        
        if not self.active:
            logger.warning(f"Scraper {source_name} is not active")
    
    def _get_source_config(self) -> Dict[str, Any]:
        """
        Get source configuration from settings.
        """
        if self.source_name not in settings.ANIME_SOURCES:
            logger.error(f"Source {self.source_name} not found in settings")
            return {}
        return settings.ANIME_SOURCES[self.source_name]
    
    def get_html(self, url: str, headers: Optional[Dict[str, str]] = None) -> str:
        """
        Get HTML content from URL.
        """
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting HTML from {url}: {e}")
            raise
    
    def get_soup(self, url: str, headers: Optional[Dict[str, str]] = None) -> BeautifulSoup:
        """
        Get BeautifulSoup object from URL.
        """
        html = self.get_html(url, headers)
        return BeautifulSoup(html, "lxml")
    
    def get_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Get JSON from URL.
        """
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting JSON from {url}: {e}")
            raise
        except ValueError as e:
            logger.error(f"Error parsing JSON from {url}: {e}")
            raise
    
    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for anime.
        """
        pass
    
    @abstractmethod
    def get_anime_details(self, anime_slug: str) -> Dict[str, Any]:
        """
        Get anime details.
        """
        pass
    
    @abstractmethod
    def get_episode_details(self, episode_url: str) -> Dict[str, Any]:
        """
        Get episode details.
        """
        pass
    
    @abstractmethod
    def get_anime_terbaru(self, page: int = 1) -> List[Dict[str, Any]]:
        """
        Get latest anime.
        """
        pass
    
    @abstractmethod
    def get_movie_list(self, page: int = 1) -> List[Dict[str, Any]]:
        """
        Get movie list.
        """
        pass
    
    @abstractmethod
    def get_jadwal_rilis(self, day: Optional[str] = None) -> Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]:
        """
        Get release schedule.
        """
        pass
    
    @abstractmethod
    def get_home_data(self) -> Dict[str, Any]:
        """
        Get home page data.
        """
        pass