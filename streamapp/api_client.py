import logging
import requests
from typing import Any, Dict, List, Optional, Union, Tuple
import json
import os
import time
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

def get_api_endpoints():
    """
    Get active API endpoints from database, ordered by priority.
    
    Returns:
        List of APIEndpoint objects
    """
    # Import here to avoid circular import
    from .models import APIEndpoint
    from django.db.utils import OperationalError
    
    # Selalu ambil dari database untuk memastikan data terbaru
    # Ini memastikan perubahan status aktif langsung terlihat
    try:
        # Ambil langsung dari database, jangan gunakan cache
        endpoints = list(APIEndpoint.objects.filter(is_active=True).order_by('-priority'))
        
        # Filter endpoint yang tidak berfungsi
        working_endpoints = []
        for endpoint in endpoints:
            # Periksa apakah endpoint berfungsi dengan mencoba mengakses /anime-terbaru
            try:
                url = f"{endpoint.url.rstrip('/')}/anime-terbaru"
                logger.info(f"Checking if endpoint {endpoint.name} ({url}) is working...")
                response = requests.get(url, timeout=3)
                if response.status_code >= 200 and response.status_code < 300:
                    logger.info(f"Endpoint {endpoint.name} ({url}) is working")
                    working_endpoints.append(endpoint)
                else:
                    logger.warning(f"Endpoint {endpoint.name} ({url}) returned status code {response.status_code}")
            except Exception as e:
                logger.warning(f"Endpoint {endpoint.name} ({endpoint.url}) is not working: {e}")
        
        # Jika ada endpoint yang berfungsi, gunakan itu
        if working_endpoints:
            logger.info(f"Using {len(working_endpoints)} working endpoints")
            endpoints = working_endpoints
        
        # Jika tidak ada endpoint aktif, gunakan default
        if not endpoints:
            default_url = getattr(settings, "API_BASE_URL", "http://localhost:8001/api/v1")
            logger.warning(f"No active API endpoints found in database, using default: {default_url}")
            endpoints = [create_temp_endpoint(default_url)]
    except OperationalError as e:
        # Handle case when table doesn't exist yet (during migrations)
        logger.warning(f"Error accessing APIEndpoint table (likely during migrations): {e}")
        default_url = getattr(settings, "API_BASE_URL", "http://localhost:8001/api/v1")
        logger.info(f"Using default API endpoint: {default_url}")
        endpoints = [create_temp_endpoint(default_url)]
    
    return endpoints

def create_temp_endpoint(url, name="Default", source_domain="v1.samehadaku.how"):
    """
    Create a temporary endpoint object.
    
    Args:
        url: API endpoint URL
        name: API endpoint name
        source_domain: Domain sumber data
        
    Returns:
        Temporary endpoint object
    """
    class TempEndpoint:
        def __init__(self, url, name, source_domain):
            self.url = url
            self.name = name
            self.source_domain = source_domain
    
    return TempEndpoint(url, name, source_domain)


class FallbackAPIClient:
    """
    Client for interacting with multiple FastAPI backends with fallback support.
    This client is stateful and will handle multi-level fallbacks automatically.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "KortekStream Django Client",
            "Accept": "application/json",
        })
        self.connect_timeout = 3
        self.read_timeout = 10
        self.endpoints = []
        self.current_endpoint_index = 0

    def refresh_endpoints(self):
        """
        Refresh the list of endpoints from the database and reset the client's state.
        """
        logger.info("Refreshing API endpoints list...")
        self.endpoints = get_api_endpoints()
        self.current_endpoint_index = 0
        if not self.endpoints:
            logger.critical("No active API endpoints found!")
        else:
            logger.info(f"{len(self.endpoints)} active endpoints loaded. Primary API is '{self.endpoints[0].name}'.")

    def _fallback_to_next_endpoint(self):
        """
        Handles the core fallback logic: clear cache, move to the next API.
        Returns True if fallback was successful, False otherwise.
        """
        # Clear all Django cache immediately on any failure that triggers a fallback.
        logger.warning("API failure detected. Clearing all cache to prevent stale data.")
        cache.clear()

        if self.current_endpoint_index + 1 < len(self.endpoints):
            old_api_name = self.endpoints[self.current_endpoint_index].name
            self.current_endpoint_index += 1
            new_api_name = self.endpoints[self.current_endpoint_index].name
            logger.warning(f"FALLBACK ACTIVATED: Switching from '{old_api_name}' to '{new_api_name}'.")
            return True
        else:
            logger.critical("All available API endpoints have failed. No more fallbacks available.")
            return False

    def _handle_response(self, response: requests.Response) -> Any:
        """
        Handles API response, checking for HTTP errors and low confidence scores.
        """
        current_endpoint = self.get_current_endpoint()
        current_endpoint_name = current_endpoint.name if current_endpoint else "Unknown"
        try:
            response.raise_for_status()
            data = response.json()
            
            confidence_score = data.get("confidence_score", 1.0)
            if confidence_score < 0.5:
                logger.warning(f"Confidence score from '{current_endpoint_name}' is too low ({confidence_score}). Triggering fallback.")
                raise Exception(f"Confidence score too low: {confidence_score}")
            
            return data
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from '{current_endpoint_name}': {e}")
            raise Exception(f"API HTTP error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from '{current_endpoint_name}': {e}")
            raise Exception(f"JSON decode error: {e}")

    def get_current_endpoint(self) -> Any:
        """
        Safely gets the current endpoint object.
        """
        if not self.endpoints or self.current_endpoint_index >= len(self.endpoints):
            return None
        return self.endpoints[self.current_endpoint_index]

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, is_retry: bool = False) -> Any:
        """
        Make a GET request. Handles fallbacks and retries automatically.
        """
        if not is_retry:
            self.refresh_endpoints()

        api_endpoint = self.get_current_endpoint()
        if not api_endpoint:
            raise Exception("No API endpoint configured after refresh.")

        request_params = params.copy() if params else {}
        if is_retry:
            request_params['force_refresh'] = True
            logger.info(f"This is a fallback retry. Forcing cache refresh on '{api_endpoint.name}'.")

        url = f"{api_endpoint.url.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.info(f"Trying GET {url} with params {request_params}")

        try:
            start_time = time.time()
            response = self.session.get(url, params=request_params, timeout=(self.connect_timeout, self.read_timeout))
            
            result = self._handle_response(response)
            
            # Success
            response_time = (time.time() - start_time) * 1000
            logger.info(f"Successfully got response from {url} in {response_time:.2f}ms")
            self._update_api_monitor(api_endpoint, endpoint, "up", response_time=response_time)
            return result

        except Exception as e:
            logger.warning(f"Request to '{api_endpoint.name}' failed: {e}")
            self._update_api_monitor(api_endpoint, endpoint, "error", error_message=str(e))
            
            if self._fallback_to_next_endpoint():
                # Automatically retry the request with the new endpoint
                return self.get(endpoint, params, is_retry=True)
            else:
                raise Exception("All API endpoints failed.")

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, is_retry: bool = False) -> Any:
        """
        Make a POST request. Handles fallbacks and retries automatically.
        """
        if not is_retry:
            self.refresh_endpoints()

        api_endpoint = self.get_current_endpoint()
        if not api_endpoint:
            raise Exception("No API endpoint configured after refresh.")

        request_data = data.copy() if data else {}
        if is_retry:
            request_data['force_refresh'] = True
            logger.info(f"This is a fallback retry. Forcing cache refresh on '{api_endpoint.name}'.")

        url = f"{api_endpoint.url.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.info(f"Trying POST {url}")

        try:
            start_time = time.time()
            response = self.session.post(url, json=request_data, timeout=(self.connect_timeout, self.read_timeout))

            result = self._handle_response(response)

            # Success
            response_time = (time.time() - start_time) * 1000
            logger.info(f"Successfully got response from {url} in {response_time:.2f}ms")
            self._update_api_monitor(api_endpoint, endpoint, "up", response_time=response_time)
            return result

        except Exception as e:
            logger.warning(f"Request to '{api_endpoint.name}' failed: {e}")
            self._update_api_monitor(api_endpoint, endpoint, "error", error_message=str(e))
            
            if self._fallback_to_next_endpoint():
                # Automatically retry the request with the new endpoint
                return self.post(endpoint, data, is_retry=True)
            else:
                raise Exception("All API endpoints failed.")

    def _update_api_monitor(self, endpoint, endpoint_path: str, status: str,
                           response_time: Optional[float] = None,
                           error_message: Optional[str] = None,
                           response_data: Optional[str] = None):
        """
        Update API monitor with status and metrics.
        """
        try:
            from .models import APIMonitor
            if not hasattr(endpoint, 'id'):
                return
            
            from django.db import transaction
            with transaction.atomic():
                monitor, created = APIMonitor.objects.get_or_create(
                    endpoint=endpoint,
                    endpoint_path=endpoint_path,
                    defaults={'status': status, 'response_time': response_time, 'error_message': error_message, 'response_data': response_data}
                )
                if not created:
                    monitor.status = status
                    monitor.response_time = response_time
                    monitor.error_message = error_message
                    monitor.response_data = response_data
                    monitor.last_checked = timezone.now()
                    monitor.save()
        except Exception as e:
            logger.error(f"Error updating API monitor: {e}")

    def get_current_api_info(self):
        """
        Mendapatkan informasi tentang API yang sedang digunakan.
        """
        current_endpoint = self.get_current_endpoint()
        if not current_endpoint:
            return {
                "status": "error",
                "message": "Tidak ada API endpoint yang dikonfigurasi.",
                "endpoint": None,
            }
        
        return {
            "status": "up",
            "message": "API sedang beroperasi.",
            "endpoint": {
                "name": current_endpoint.name,
                "url": current_endpoint.url,
                "priority": current_endpoint.priority,
                "source_domain": getattr(current_endpoint, 'source_domain', 'N/A')
            }
        }


# Create a singleton instance
api_client = FallbackAPIClient()

def get_current_api_info():
    """
    Mendapatkan informasi tentang API yang sedang digunakan.
    
    Returns:
        Dict berisi informasi tentang API yang sedang digunakan
    """
    return api_client.get_current_api_info()


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
        
        if result:
            logger.info(f"Berhasil mendapatkan data anime: {anime_slug}")
            return result
        else:
            logger.warning(f"API mengembalikan data kosong untuk anime: {anime_slug}")
            logger.info(f"Data anime tidak ditemukan untuk slug: {anime_slug}")
            return {
                "error": True,
                "message": f"Anime dengan slug '{anime_slug}' tidak ditemukan",
                "title": f"Anime {anime_slug}",
                "thumbnail_url": "/static/img/kortekstream-logo.png",
                "url_cover": "/static/img/kortekstream-logo.png",
                "sinopsis": "Data anime tidak ditemukan. Silakan coba lagi nanti atau kembali ke beranda.",
                "genres": [],
                "details": {"Status": "Unknown"},
                "episode_list": []
            }
    except Exception as e:
        logger.error(f"Error getting anime detail: {e}", exc_info=True)
        # Tambahkan informasi lebih detail untuk debugging
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Jika tidak ada data cache, gunakan data placeholder
        logger.info(f"Data anime tidak ditemukan untuk slug: {anime_slug}")
        return {
            "error": True,
            "message": f"Terjadi kesalahan saat memuat data anime: {str(e)}",
            "title": f"Anime {anime_slug}",
            "thumbnail_url": "/static/img/kortekstream-logo.png",
            "url_cover": "/static/img/kortekstream-logo.png",
            "sinopsis": "Terjadi kesalahan saat memuat data. Silakan coba lagi nanti atau kembali ke beranda.",
            "genres": [],
            "details": {"Status": "Unknown"},
            "episode_list": []
        }


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