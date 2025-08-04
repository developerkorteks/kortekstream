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

def normalize_api_response(data: Any, endpoint_name: str = "unknown") -> Any:
    """
    Normalize API response to handle different JSON structures between gomunime and samehadaku.
    
    Args:
        data: Raw API response data
        endpoint_name: Name of the API endpoint for logging
        
    Returns:
        Normalized data structure
    """
    if not data:
        return data
    
    # Jika data adalah dict dan memiliki confidence_score
    if isinstance(data, dict) and 'confidence_score' in data:
        confidence = data.get('confidence_score', 0)
        logger.info(f"API {endpoint_name} response with confidence score: {confidence}")
        
        # Jika ada field 'data', gunakan itu (gomunime format)
        if 'data' in data:
            logger.info(f"Using gomunime format (with 'data' wrapper) for {endpoint_name}")
            return data.get('data', {})
        # Jika tidak ada field 'data', gunakan data langsung (samehadaku format)
        else:
            logger.info(f"Using samehadaku format (direct data) for {endpoint_name}")
            return data
    
    # Jika data bukan dict atau tidak memiliki confidence_score, kembalikan as-is
    return data

def check_endpoint_health(endpoint):
    """
    Check if endpoint is actually working by testing health endpoint.
    
    Args:
        endpoint: APIEndpoint object or TempEndpoint
        
    Returns:
        bool: True if endpoint is working, False otherwise
    """
    try:
        # Try the base URL with /health first
        base_url = endpoint.url.rstrip('/')
        if base_url.endswith('/api/v1'):
            base_url = base_url.replace('/api/v1', '')
        
        health_url = f"{base_url}/health"
        logger.info(f"Checking health of endpoint {endpoint.name} at {health_url}")
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            try:
                health_data = response.json()
                if health_data.get('status') == 'ok':
                    logger.info(f"Endpoint {endpoint.name} is healthy")
                    return True
            except json.JSONDecodeError:
                logger.warning(f"Endpoint {endpoint.name} returned non-JSON health response")
                return False
        
        logger.warning(f"Endpoint {endpoint.name} health check failed with status {response.status_code}")
        return False
    except Exception as e:
        logger.warning(f"Endpoint {endpoint.name} health check failed: {e}")
        return False

def should_fallback(response_data, confidence_threshold=0.5):
    """
    Check if we should fallback based on confidence score or data quality.
    
    Args:
        response_data: API response data
        confidence_threshold: Minimum confidence score required
        
    Returns:
        bool: True if should fallback, False otherwise
    """
    if not response_data:
        logger.info("Response data is empty, should fallback")
        return True
    
    # Check if response has confidence_score
    if isinstance(response_data, dict) and 'confidence_score' in response_data:
        confidence = response_data.get('confidence_score', 0)
        logger.info(f"Response has confidence_score: {confidence}")
        
        if confidence < confidence_threshold:
            logger.info(f"Confidence score {confidence} below threshold {confidence_threshold}, should fallback")
            return True
        
        # Check if data field exists and has content
        if 'data' in response_data:
            data = response_data.get('data')
            if not data or (isinstance(data, list) and len(data) == 0):
                logger.info("Data field is empty, should fallback")
                return True
        else:
            # Direct data format - check if main data is empty
            if isinstance(response_data, dict):
                # Remove confidence_score and other metadata
                data_keys = [k for k in response_data.keys() if k not in ['confidence_score', 'message', 'source', 'error']]
                if not data_keys:
                    logger.info("No data keys found, should fallback")
                    return True
                
                # Check if any data key has content
                has_content = False
                for key in data_keys:
                    value = response_data.get(key)
                    if value and (not isinstance(value, list) or len(value) > 0):
                        has_content = True
                        break
                
                if not has_content:
                    logger.info("No content in data keys, should fallback")
                    return True
    
    return False

def clear_cache_on_failure(endpoint_name):
    """
    Clear cache when endpoint fails to ensure fresh data on next request.
    
    Args:
        endpoint_name: Name of the failed endpoint
    """
    cache_keys = [
        f"api_response_{endpoint_name}",
        "api_endpoints",
        "template_filter_source_domain",
        "current_source_domain"
    ]
    
    for key in cache_keys:
        cache.delete(key)
        logger.info(f"Cleared cache key: {key}")

def get_api_endpoints():
    """
    Get active API endpoints from database, ordered by priority.
    Includes health checking to filter out non-working endpoints.
    
    Returns:
        List of APIEndpoint objects
    """
    # Import here to avoid circular import
    from .models import APIEndpoint
    from django.db.utils import OperationalError
    
    try:
        # Force refresh cache to get latest data
        APIEndpoint.force_refresh_cache()
        
        # Get all active endpoints from database
        all_endpoints = list(APIEndpoint.objects.filter(is_active=True).order_by('-priority'))
        logger.info(f"Found {len(all_endpoints)} active endpoints in database")
        
        # Health check all endpoints
        working_endpoints = []
        failed_endpoints = []
        
        for endpoint in all_endpoints:
            if check_endpoint_health(endpoint):
                working_endpoints.append(endpoint)
            else:
                failed_endpoints.append(endpoint)
                # Mark endpoint as inactive if it's consistently failing
                logger.warning(f"Marking endpoint {endpoint.name} as inactive due to health check failure")
                endpoint.is_active = False
                endpoint.save()
        
        logger.info(f"Health check results: {len(working_endpoints)} working, {len(failed_endpoints)} failed")
        
        # Use working endpoints if available
        if working_endpoints:
            logger.info(f"Using {len(working_endpoints)} working endpoints")
            return working_endpoints
        
        # If no working endpoints, use default
        default_url = getattr(settings, "API_BASE_URL", "http://localhost:8080/api/v1")
        logger.warning(f"No working API endpoints found, using default: {default_url}")
        return [create_temp_endpoint(default_url)]
        
    except OperationalError as e:
        logger.error(f"Database error getting API endpoints: {e}")
        return []
    except Exception as e:
        logger.error(f"Error getting API endpoints: {e}")
        return []

def create_temp_endpoint(url, name="Default", source_domain=None):
    """
    Create a temporary endpoint object.
    
    Args:
        url: API endpoint URL
        name: API endpoint name
        source_domain: Domain sumber data (optional)
        
    Returns:
        Temporary endpoint object
    """
    class TempEndpoint:
        def __init__(self, url, name, source_domain):
            self.url = url
            self.name = name
            self.source_domain = source_domain or "gomunime.co"
            # Add missing attributes that are expected by the monitoring system
            self.priority = 0  # Default priority for temp endpoints
            self.is_active = True
            self.last_used = None
            self.success_count = 0
            self.id = None  # Temp endpoints don't have database ID
        
        def save(self):
            """Dummy save method for temp endpoints - they don't persist to database"""
            pass
    
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
        
        # Clear all caches comprehensively
        from .models import APIEndpoint
        APIEndpoint.force_refresh_cache()
        
        # Force refresh endpoints list
        self.refresh_endpoints()

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
        Handle API response and extract data.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed response data
            
        Raises:
            Exception: If response cannot be parsed
        """
        try:
            # Check if response is empty
            if not response.text.strip():
                raise Exception("Empty response received")
            
            # Try to parse JSON
            data = response.json()
            
            # Check if response contains error
            if isinstance(data, dict) and data.get('error'):
                raise Exception(f"API error: {data.get('message', 'Unknown error')}")
            
            return data
            
        except requests.exceptions.JSONDecodeError as e:
            # Log the actual response for debugging
            logger.error(f"JSON decode error from '{self.get_current_endpoint().name}': {e}")
            logger.error(f"Response status: {response.status_code}")
            logger.error(f"Response text: {response.text[:500]}...")  # Log first 500 chars
            
            # If response is not JSON, it might be HTML error page
            if 'html' in response.headers.get('content-type', '').lower():
                raise Exception(f"Received HTML instead of JSON (status: {response.status_code})")
            
            raise Exception(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            raise

    def get_current_endpoint(self) -> Any:
        """
        Safely gets the current endpoint object.
        """
        if not self.endpoints or self.current_endpoint_index >= len(self.endpoints):
            return None
        return self.endpoints[self.current_endpoint_index]

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, is_retry: bool = False) -> Any:
        """
        Make a GET request to the API with improved fallback support.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            is_retry: Whether this is a retry attempt
            
        Returns:
            API response data
            
        Raises:
            Exception: If all endpoints fail
        """
        if not is_retry:
            # Force refresh endpoints on first attempt
            self.refresh_endpoints()
        
        if not self.endpoints:
            raise Exception("No API endpoints available")
        
        # Get current endpoint
        current_endpoint = self.get_current_endpoint()
        if not current_endpoint:
            raise Exception("No current endpoint available")
        
        # Build URL with current endpoint
        url = f"{current_endpoint.url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Prepare request parameters
        request_params = params or {}
        
        try:
            logger.info(f"Making request to '{current_endpoint.name}' at {url}")
            response = self.session.get(url, params=request_params, timeout=(self.connect_timeout, self.read_timeout))
            
            # Handle response and check for fallback conditions
            response_data = self._handle_response(response)
            
            # Check if we should fallback based on confidence score or data quality
            if should_fallback(response_data):
                logger.warning(f"Response from {current_endpoint.name} has low confidence or empty data, trying fallback")
                # Clear cache and try next endpoint
                clear_cache_on_failure(current_endpoint.name)
                if not is_retry:
                    self._fallback_to_next_endpoint()
                    return self.get(endpoint, params, is_retry=True)
                else:
                    # If this is a retry and we still have endpoints, try the next one
                    if self.current_endpoint_index < len(self.endpoints) - 1:
                        self._fallback_to_next_endpoint()
                        return self.get(endpoint, params, is_retry=True)
                    else:
                        # All endpoints have failed
                        logger.error("All API endpoints failed or returned low quality data.")
                        raise Exception("All API endpoints failed or returned low quality data.")
            
            # Success - update endpoint usage
            if hasattr(current_endpoint, 'save'):
                current_endpoint.last_used = timezone.now()
                current_endpoint.success_count += 1
                current_endpoint.save()
            
            # Update API monitor
            self._update_api_monitor(current_endpoint, endpoint, "success", response_time=None)
            
            logger.info(f"Successfully got data from {current_endpoint.name} for endpoint {endpoint}")
            return response_data

        except Exception as e:
            logger.warning(f"Request to '{current_endpoint.name}' failed: {e}")
            self._update_api_monitor(current_endpoint, endpoint, "error", error_message=str(e))
            
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
            # Force refresh endpoints on first attempt
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

                # Update last_used and success_count on the APIEndpoint
                if status == "up":
                    endpoint.last_used = timezone.now()
                    endpoint.success_count = (endpoint.success_count or 0) + 1
                    endpoint.save()
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
        
        # Normalize response untuk menangani perbedaan struktur JSON
        normalized_result = normalize_api_response(result, endpoint)
        
        # Validasi hasil
        if day is None and not normalized_result:
            logger.warning("API mengembalikan data kosong untuk jadwal rilis")
        elif day and not normalized_result:
            logger.warning(f"API mengembalikan data kosong untuk jadwal rilis hari {day}")
        
        return normalized_result
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
        
        # Normalize response untuk menangani perbedaan struktur JSON
        normalized_result = normalize_api_response(result, "anime-terbaru")
        
        # Validasi hasil
        if not normalized_result:
            logger.warning(f"API mengembalikan data kosong untuk anime terbaru halaman {page}")
        else:
            logger.info(f"Berhasil mendapatkan {len(normalized_result)} anime terbaru")
        
        return normalized_result
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
        
        # Normalize response untuk menangani perbedaan struktur JSON
        normalized_result = normalize_api_response(result, "movie")
        
        # Validasi hasil
        if not normalized_result:
            logger.warning(f"API mengembalikan data kosong untuk daftar movie halaman {page}")
        else:
            logger.info(f"Berhasil mendapatkan {len(normalized_result)} movie")
        
        return normalized_result
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
        
        # Normalize response untuk menangani perbedaan struktur JSON
        normalized_result = normalize_api_response(result, "anime-detail")
        
        if normalized_result:
            logger.info(f"Berhasil mendapatkan data anime: {anime_slug}")
            return normalized_result
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
        
        # Normalize response untuk menangani perbedaan struktur JSON
        normalized_result = normalize_api_response(result, "episode-detail")
        
        if not normalized_result:
            logger.warning(f"API mengembalikan data kosong untuk episode: {episode_url}")
        return normalized_result
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
        
        # Normalize response untuk menangani perbedaan struktur JSON
        normalized_result = normalize_api_response(result, "search")
        
        if not normalized_result:
            logger.warning(f"API mengembalikan data kosong untuk pencarian: {query}")
        return normalized_result
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
        
        # Normalize response untuk menangani perbedaan struktur JSON
        normalized_result = normalize_api_response(result, "home")
        
        # Validasi hasil
        if not normalized_result:
            logger.warning("API mengembalikan data kosong untuk halaman utama")
        else:
            # Log jumlah item yang diterima untuk setiap bagian
            logger.info(f"Data diterima - Top 10: {len(normalized_result.get('top10', []))}, " +
                       f"New Eps: {len(normalized_result.get('new_eps', []))}, " +
                       f"Movies: {len(normalized_result.get('movies', []))}, " +
                       f"Jadwal: {len(normalized_result.get('jadwal_rilis', {}).keys())}")
        
        return normalized_result
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