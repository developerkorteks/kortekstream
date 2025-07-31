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

def create_temp_endpoint(url, name="Default"):
    """
    Create a temporary endpoint object.
    
    Args:
        url: API endpoint URL
        name: API endpoint name
        
    Returns:
        Temporary endpoint object
    """
    class TempEndpoint:
        def __init__(self, url, name):
            self.url = url
            self.name = name
    
    return TempEndpoint(url, name)


class FallbackAPIClient:
    """
    Client for interacting with multiple FastAPI backends with fallback support.
    """
    def __init__(self):
        self.endpoints = get_api_endpoints()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "KortekStream Django Client",
            "Accept": "application/json",
        })
        # Cache for failed endpoints to avoid retrying too often
        self.failed_endpoints = {}
        # Default timeout values
        self.connect_timeout = 3  # seconds
        self.read_timeout = 10    # seconds
        # Informasi tentang API yang sedang digunakan
        self.current_api = {
            "endpoint": None,
            "last_used": None,
            "success_count": 0,
            "error_log": []
        }
    
    def refresh_endpoints(self):
        """
        Refresh the list of endpoints from database.
        """
        # Ambil langsung dari database untuk memastikan data terbaru
        self.endpoints = get_api_endpoints()
        # Reset failed endpoints cache
        self.failed_endpoints = {}
        logger.info(f"Endpoint list refreshed, {len(self.endpoints)} active endpoints found")
    
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
    
    def _should_retry_endpoint(self, endpoint_url: str) -> bool:
        """
        Check if we should retry a previously failed endpoint.
        
        Args:
            endpoint_url: URL of the endpoint
            
        Returns:
            True if we should retry, False otherwise
        """
        if endpoint_url not in self.failed_endpoints:
            return True
        
        # Get last failure time and count
        last_failure, failure_count = self.failed_endpoints[endpoint_url]
        
        # Calculate backoff time based on failure count (exponential backoff)
        backoff_time = min(60 * 5, 2 ** failure_count)  # Max 5 minutes
        
        # Check if enough time has passed since last failure
        time_passed = time.time() - last_failure
        return time_passed > backoff_time
    
    def _mark_endpoint_failed(self, endpoint_url: str):
        """
        Mark an endpoint as failed.
        
        Args:
            endpoint_url: URL of the endpoint
        """
        if endpoint_url in self.failed_endpoints:
            last_failure, failure_count = self.failed_endpoints[endpoint_url]
            self.failed_endpoints[endpoint_url] = (time.time(), failure_count + 1)
        else:
            self.failed_endpoints[endpoint_url] = (time.time(), 1)
    
    def _mark_endpoint_success(self, endpoint_url: str):
        """
        Mark an endpoint as successful.
        
        Args:
            endpoint_url: URL of the endpoint
        """
        if endpoint_url in self.failed_endpoints:
            del self.failed_endpoints[endpoint_url]
    
    def _update_api_monitor(self, endpoint, endpoint_path: str, status: str,
                           response_time: Optional[float] = None,
                           error_message: Optional[str] = None,
                           response_data: Optional[str] = None):
        """
        Update API monitor with status and metrics.
        
        Args:
            endpoint: APIEndpoint object
            endpoint_path: API endpoint path
            status: Status of the request (up, down, error, timeout)
            response_time: Response time in milliseconds
            error_message: Error message if any
            response_data: Response data if any
        """
        try:
            # Import here to avoid circular import
            from .models import APIMonitor
            
            # Check if endpoint is a temporary object
            if not hasattr(endpoint, 'id'):
                return
            
            # Update monitor asynchronously to avoid blocking
            from django.db import transaction
            with transaction.atomic():
                monitor, created = APIMonitor.objects.get_or_create(
                    endpoint=endpoint,
                    endpoint_path=endpoint_path,
                    defaults={
                        'status': status,
                        'response_time': response_time,
                        'error_message': error_message,
                        'response_data': response_data
                    }
                )
                
                if not created:
                    monitor.status = status
                    monitor.response_time = response_time
                    monitor.error_message = error_message
                    monitor.response_data = response_data
                    monitor.save()
        except Exception as e:
            logger.error(f"Error updating API monitor: {e}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make GET request to API with fallback support.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data
            
        Raises:
            Exception: If all API endpoints fail
        """
        # Refresh endpoints list to ensure we have the latest active endpoints
        self.refresh_endpoints()
        
        # Try each endpoint in order of priority
        last_exception = None
        tried_endpoints = []
        
        for api_endpoint in self.endpoints:
            # Skip endpoints that have failed recently
            if not self._should_retry_endpoint(api_endpoint.url):
                logger.debug(f"Skipping recently failed endpoint: {api_endpoint.url}")
                continue
            
            url = f"{api_endpoint.url.rstrip('/')}/{endpoint.lstrip('/')}"
            logger.info(f"Trying GET {url} {params}")
            tried_endpoints.append(api_endpoint.url)
            
            try:
                start_time = time.time()
                response = self.session.get(
                    url,
                    params=params,
                    timeout=(self.connect_timeout, self.read_timeout)
                )
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Handle response
                result = self._handle_response(response)
                
                # Mark endpoint as successful
                self._mark_endpoint_success(api_endpoint.url)
                
                # Update API monitor
                self._update_api_monitor(
                    api_endpoint,
                    endpoint,
                    "up",
                    response_time,
                    response_data=json.dumps(result)[:1000] if result else None
                )
                
                # Update current API information
                self.current_api = {
                    "endpoint": api_endpoint,
                    "last_used": timezone.now(),
                    "success_count": self.current_api.get("success_count", 0) + 1,
                    "error_log": self.current_api.get("error_log", [])
                }
                
                logger.info(f"Successfully got response from {url}")
                return result
                
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout in GET {url}: {e}")
                self._mark_endpoint_failed(api_endpoint.url)
                self._update_api_monitor(api_endpoint, endpoint, "timeout", None, str(e))
                # Log error
                error_entry = {
                    "timestamp": timezone.now(),
                    "endpoint": api_endpoint.name,
                    "url": url,
                    "type": "timeout",
                    "message": str(e)
                }
                self.current_api["error_log"] = self.current_api.get("error_log", [])[-9:] + [error_entry]
                last_exception = e
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error in GET {url}: {e}")
                self._mark_endpoint_failed(api_endpoint.url)
                self._update_api_monitor(api_endpoint, endpoint, "down", None, str(e))
                # Log error
                error_entry = {
                    "timestamp": timezone.now(),
                    "endpoint": api_endpoint.name,
                    "url": url,
                    "type": "connection",
                    "message": str(e)
                }
                self.current_api["error_log"] = self.current_api.get("error_log", [])[-9:] + [error_entry]
                last_exception = e
                
            except Exception as e:
                logger.warning(f"Error in GET {url}: {e}")
                self._mark_endpoint_failed(api_endpoint.url)
                self._update_api_monitor(api_endpoint, endpoint, "error", None, str(e))
                # Log error
                error_entry = {
                    "timestamp": timezone.now(),
                    "endpoint": api_endpoint.name,
                    "url": url,
                    "type": "error",
                    "message": str(e)
                }
                self.current_api["error_log"] = self.current_api.get("error_log", [])[-9:] + [error_entry]
                last_exception = e
        
        # If we get here, all endpoints failed
        logger.error(f"All API endpoints failed for GET {endpoint}: {tried_endpoints}")
        if last_exception:
            raise Exception(f"All API endpoints failed: {str(last_exception)}")
        else:
            raise Exception("All API endpoints failed")
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make POST request to API with fallback support.
        
        Args:
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response data
            
        Raises:
            Exception: If all API endpoints fail
        """
        # Refresh endpoints list to ensure we have the latest active endpoints
        self.refresh_endpoints()
        
        # Try each endpoint in order of priority
        last_exception = None
        tried_endpoints = []
        
        for api_endpoint in self.endpoints:
            # Skip endpoints that have failed recently
            if not self._should_retry_endpoint(api_endpoint.url):
                logger.debug(f"Skipping recently failed endpoint: {api_endpoint.url}")
                continue
            
            url = f"{api_endpoint.url.rstrip('/')}/{endpoint.lstrip('/')}"
            logger.info(f"Trying POST {url}")
            tried_endpoints.append(api_endpoint.url)
            
            try:
                start_time = time.time()
                response = self.session.post(
                    url,
                    json=data,
                    timeout=(self.connect_timeout, self.read_timeout)
                )
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Handle response
                result = self._handle_response(response)
                
                # Mark endpoint as successful
                self._mark_endpoint_success(api_endpoint.url)
                
                # Update API monitor
                self._update_api_monitor(
                    api_endpoint,
                    endpoint,
                    "up",
                    response_time,
                    response_data=json.dumps(result)[:1000] if result else None
                )
                
                # Update current API information
                self.current_api = {
                    "endpoint": api_endpoint,
                    "last_used": timezone.now(),
                    "success_count": self.current_api.get("success_count", 0) + 1,
                    "error_log": self.current_api.get("error_log", [])
                }
                
                logger.info(f"Successfully got response from {url}")
                return result
                
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout in POST {url}: {e}")
                self._mark_endpoint_failed(api_endpoint.url)
                self._update_api_monitor(api_endpoint, endpoint, "timeout", None, str(e))
                # Log error
                error_entry = {
                    "timestamp": timezone.now(),
                    "endpoint": api_endpoint.name,
                    "url": url,
                    "type": "timeout",
                    "message": str(e)
                }
                self.current_api["error_log"] = self.current_api.get("error_log", [])[-9:] + [error_entry]
                last_exception = e
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error in POST {url}: {e}")
                self._mark_endpoint_failed(api_endpoint.url)
                self._update_api_monitor(api_endpoint, endpoint, "down", None, str(e))
                # Log error
                error_entry = {
                    "timestamp": timezone.now(),
                    "endpoint": api_endpoint.name,
                    "url": url,
                    "type": "connection",
                    "message": str(e)
                }
                self.current_api["error_log"] = self.current_api.get("error_log", [])[-9:] + [error_entry]
                last_exception = e
                
            except Exception as e:
                logger.warning(f"Error in POST {url}: {e}")
                self._mark_endpoint_failed(api_endpoint.url)
                self._update_api_monitor(api_endpoint, endpoint, "error", None, str(e))
                # Log error
                error_entry = {
                    "timestamp": timezone.now(),
                    "endpoint": api_endpoint.name,
                    "url": url,
                    "type": "error",
                    "message": str(e)
                }
                self.current_api["error_log"] = self.current_api.get("error_log", [])[-9:] + [error_entry]
                last_exception = e
        
        # If we get here, all endpoints failed
        logger.error(f"All API endpoints failed for POST {endpoint}: {tried_endpoints}")
        if last_exception:
            raise Exception(f"All API endpoints failed: {str(last_exception)}")
        else:
            raise Exception("All API endpoints failed")


    def get_current_api_info(self):
        """
        Mendapatkan informasi tentang API yang sedang digunakan.
        
        Returns:
            Dict berisi informasi tentang API yang sedang digunakan
        """
        if not self.current_api.get("endpoint"):
            return {
                "status": "not_used",
                "message": "Belum ada API yang digunakan",
                "endpoint": None,
                "last_used": None,
                "success_count": 0,
                "error_log": []
            }
        
        endpoint = self.current_api.get("endpoint")
        
        # Cek status endpoint
        status = "unknown"
        message = "Status tidak diketahui"
        
        if endpoint:
            # Import di sini untuk menghindari circular import
            from .models import APIMonitor
            
            try:
                # Cek monitor terbaru untuk endpoint ini
                monitors = APIMonitor.objects.filter(endpoint=endpoint).order_by('-last_checked')
                
                if monitors.exists():
                    # Hitung jumlah status untuk endpoint ini
                    status_counts = {}
                    for monitor in monitors:
                        status_counts[monitor.status] = status_counts.get(monitor.status, 0) + 1
                    
                    # Tentukan status berdasarkan mayoritas
                    if status_counts.get('up', 0) > status_counts.get('down', 0) + status_counts.get('error', 0) + status_counts.get('timeout', 0):
                        status = "up"
                        message = "API berfungsi dengan baik"
                    elif status_counts.get('down', 0) > 0:
                        status = "down"
                        message = "API tidak dapat diakses"
                    elif status_counts.get('error', 0) > 0:
                        status = "error"
                        message = "API mengembalikan error"
                    elif status_counts.get('timeout', 0) > 0:
                        status = "timeout"
                        message = "API timeout"
                    else:
                        status = "unknown"
                        message = "Status tidak diketahui"
            except Exception as e:
                logger.error(f"Error saat mendapatkan status API: {e}")
                status = "error"
                message = f"Error saat mendapatkan status: {e}"
        
        return {
            "status": status,
            "message": message,
            "endpoint": {
                "name": endpoint.name,
                "url": endpoint.url,
                "priority": endpoint.priority
            } if endpoint else None,
            "last_used": self.current_api.get("last_used"),
            "success_count": self.current_api.get("success_count", 0),
            "error_log": self.current_api.get("error_log", [])
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
    # Coba ambil dari cache lokal terlebih dahulu
    cache_key = f"local_anime_detail_{anime_slug}"
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"Menggunakan data cache lokal untuk anime: {anime_slug}")
        return cached_data
    
    try:
        logger.info(f"Mengambil detail anime dengan slug: {anime_slug}")
        result = api_client.get("anime-detail", params={"anime_slug": anime_slug})
        
        if result:
            # Jika berhasil mendapatkan data, simpan ke cache lokal
            logger.info(f"Berhasil mendapatkan data anime: {anime_slug}")
            cache.set(cache_key, result, 60*60*24)  # Cache selama 24 jam
            return result
        else:
            logger.warning(f"API mengembalikan data kosong untuk anime: {anime_slug}")
            # Coba gunakan data cache lokal jika ada
            stale_cache = cache.get(f"stale_local_anime_detail_{anime_slug}")
            if stale_cache:
                logger.info(f"Menggunakan data cache lokal lama untuk anime: {anime_slug}")
                return stale_cache
            
            # Jika tidak ada data cache, coba gunakan data placeholder
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
        
        # Coba gunakan data cache lokal jika ada
        stale_cache = cache.get(f"stale_local_anime_detail_{anime_slug}")
        if stale_cache:
            logger.info(f"Menggunakan data cache lokal lama untuk anime: {anime_slug}")
            return stale_cache
        
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