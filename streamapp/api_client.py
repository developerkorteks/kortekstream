import logging
import requests
from typing import Any, Dict, List, Optional, Union
import json
import os
from django.conf import settings

logger = logging.getLogger(__name__)

# Default API URL (can be overridden in settings.py)
API_BASE_URL = getattr(settings, "API_BASE_URL", "http://localhost:8001/api/v1")


class APIClient:
    """
    Client for interacting with the FastAPI backend.
    """
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "KortekStream Django Client",
            "Accept": "application/json",
        })
    
    def _handle_response(self, response: requests.Response) -> Any:
        """
        Handle API response.
        
        Args:
            response: Response from API
            
        Returns:
            Response data
            
        Raises:
            Exception: If response status code is not 2xx
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            # Try to get error details from response
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", str(error_data))
            except:
                error_detail = response.text or str(e)
            
            logger.error(f"API error: {error_detail}")
            raise Exception(f"API error: {error_detail}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise Exception(f"Request error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise Exception(f"JSON decode error: {e}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make GET request to API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"GET {url} {params}")
        
        try:
            # Tambahkan timeout untuk mencegah request yang terlalu lama
            response = self.session.get(url, params=params, timeout=(5, 30))  # 5s connect, 30s read
            return self._handle_response(response)
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout in GET {url}: {e}")
            # Tambahkan informasi lebih detail untuk debugging
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"API timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error in GET {url}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"API connection error: {e}")
        except Exception as e:
            logger.error(f"Error in GET {url}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make POST request to API.
        
        Args:
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response data
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"POST {url}")
        
        try:
            # Tambahkan timeout untuk mencegah request yang terlalu lama
            response = self.session.post(url, json=data, timeout=(5, 30))  # 5s connect, 30s read
            return self._handle_response(response)
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout in POST {url}: {e}")
            # Tambahkan informasi lebih detail untuk debugging
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"API timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error in POST {url}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"API connection error: {e}")
        except Exception as e:
            logger.error(f"Error in POST {url}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise


# Create a singleton instance
api_client = APIClient()


# Convenience functions for API endpoints

def get_jadwal_rilis(day: Optional[str] = None) -> Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]:
    """
    Get release schedule.
    
    Args:
        day: Day of the week (optional)
        
    Returns:
        Release schedule data
    """
    endpoint = "jadwal-rilis"
    if day:
        endpoint = f"{endpoint}/{day.lower()}"
    
    try:
        logger.info(f"Mengambil jadwal rilis{' untuk hari ' + day if day else ''}")
        result = api_client.get(endpoint)
        
        # Validasi hasil
        if day is None and not result:
            logger.warning("API mengembalikan data kosong untuk jadwal rilis")
        elif day and not result:
            logger.warning(f"API mengembalikan data kosong untuk jadwal rilis hari {day}")
        
        return result
    except Exception as e:
        logger.error(f"Error getting jadwal rilis: {e}", exc_info=True)
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return {} if day is None else []


def get_anime_terbaru(page: int = 1) -> List[Dict[str, Any]]:
    """
    Get latest anime.
    
    Args:
        page: Page number
        
    Returns:
        Latest anime data
    """
    try:
        logger.info(f"Mengambil anime terbaru halaman {page}")
        result = api_client.get("anime-terbaru", params={"page": page})
        
        # Validasi hasil
        if not result:
            logger.warning(f"API mengembalikan data kosong untuk anime terbaru halaman {page}")
        else:
            logger.info(f"Berhasil mendapatkan {len(result)} anime terbaru")
        
        return result
    except Exception as e:
        logger.error(f"Error getting anime terbaru: {e}", exc_info=True)
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return []


def get_movie_list(page: int = 1) -> List[Dict[str, Any]]:
    """
    Get movie list.
    
    Args:
        page: Page number
        
    Returns:
        Movie list data
    """
    try:
        logger.info(f"Mengambil daftar movie halaman {page}")
        result = api_client.get("movie", params={"page": page})
        
        # Validasi hasil
        if not result:
            logger.warning(f"API mengembalikan data kosong untuk daftar movie halaman {page}")
        else:
            logger.info(f"Berhasil mendapatkan {len(result)} movie")
        
        return result
    except Exception as e:
        logger.error(f"Error getting movie list: {e}", exc_info=True)
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return []


def get_anime_detail(anime_slug: str) -> Dict[str, Any]:
    """
    Get anime details.
    
    Args:
        anime_slug: Anime slug
        
    Returns:
        Anime details data
    """
    try:
        logger.info(f"Mengambil detail anime dengan slug: {anime_slug}")
        result = api_client.get("anime-detail", params={"anime_slug": anime_slug})
        if not result:
            logger.warning(f"API mengembalikan data kosong untuk anime: {anime_slug}")
        return result
    except Exception as e:
        logger.error(f"Error getting anime detail: {e}", exc_info=True)
        # Tambahkan informasi lebih detail untuk debugging
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return {}


def get_episode_detail(episode_url: str) -> Dict[str, Any]:
    """
    Get episode details.
    
    Args:
        episode_url: Episode URL
        
    Returns:
        Episode details data
    """
    try:
        logger.info(f"Mengambil detail episode dengan URL: {episode_url}")
        result = api_client.get("episode-detail", params={"episode_url": episode_url})
        if not result:
            logger.warning(f"API mengembalikan data kosong untuk episode: {episode_url}")
        return result
    except Exception as e:
        logger.error(f"Error getting episode detail: {e}", exc_info=True)
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return {}


def search_anime(query: str) -> List[Dict[str, Any]]:
    """
    Search for anime.
    
    Args:
        query: Search query
        
    Returns:
        Search results
    """
    try:
        logger.info(f"Mencari anime dengan query: {query}")
        result = api_client.get("search", params={"query": query})
        if not result:
            logger.warning(f"API mengembalikan data kosong untuk pencarian: {query}")
        return result
    except Exception as e:
        logger.error(f"Error searching anime: {e}", exc_info=True)
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return []


def get_home_data() -> Dict[str, Any]:
    """
    Get home page data.
    
    Returns:
        Home page data
    """
    try:
        logger.info("Mengambil data halaman utama")
        result = api_client.get("home")
        
        # Validasi hasil
        if not result:
            logger.warning("API mengembalikan data kosong untuk halaman utama")
        else:
            # Log jumlah item yang diterima untuk setiap bagian
            logger.info(f"Data diterima - Top 10: {len(result.get('top10', []))}, " +
                       f"New Eps: {len(result.get('new_eps', []))}, " +
                       f"Movies: {len(result.get('movies', []))}, " +
                       f"Jadwal: {len(result.get('jadwal_rilis', {}).keys())}")
        
        return result
    except Exception as e:
        logger.error(f"Error getting home data: {e}", exc_info=True)
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return {
            "top10": [],
            "new_eps": [],
            "movies": [],
            "jadwal_rilis": {}
        }