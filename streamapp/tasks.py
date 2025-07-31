import logging
import time
from django.utils import timezone
from django.core.cache import cache

from .models import APIEndpoint, APIMonitor

logger = logging.getLogger(__name__)

# Daftar endpoint yang akan diperiksa
ENDPOINTS_TO_CHECK = [
    'home',
    'anime-terbaru',
    'movie',
    'jadwal-rilis',
    'search',
]

def check_api_status():
    """
    Memeriksa status semua API endpoint yang aktif.
    Fungsi ini dapat dijalankan secara periodik melalui management command atau Celery.
    """
    logger.info("Memulai pemeriksaan status API...")
    
    # Ambil semua endpoint API yang aktif
    endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
    
    if not endpoints:
        logger.warning("Tidak ada API endpoint yang aktif")
        return
    
    logger.info(f"Memeriksa {len(endpoints)} API endpoint")
    
    # Periksa setiap endpoint
    for endpoint in endpoints:
        logger.info(f"Memeriksa endpoint: {endpoint.name} ({endpoint.url})")
        
        # Periksa setiap path
        for path in ENDPOINTS_TO_CHECK:
            try:
                logger.info(f"Memeriksa path: {path}")
                
                # Gunakan metode check_endpoint dari model APIMonitor
                # Jika path adalah 'search', tambahkan parameter query
                if path == 'search':
                    # Buat URL dengan parameter query yang benar
                    search_url = f"{endpoint.url.rstrip('/')}/{path.lstrip('/')}?query=test"
                    # Panggil metode check_endpoint dengan URL khusus
                    monitor = APIMonitor.check_endpoint(endpoint, path, custom_url=search_url)
                else:
                    monitor = APIMonitor.check_endpoint(endpoint, path)
                
                logger.info(f"Status {endpoint.name}/{path}: {monitor.status}")
                
                # Jika status down, catat di log
                if monitor.status in ['down', 'error', 'timeout']:
                    logger.warning(f"API {endpoint.name}/{path} {monitor.status}: {monitor.error_message}")
                
            except Exception as e:
                logger.error(f"Error saat memeriksa {endpoint.name}/{path}: {e}")
    
    # Hapus cache untuk memaksa refresh daftar endpoint
    cache.delete("api_endpoints")
    
    logger.info("Pemeriksaan status API selesai")
    return True

def get_api_status_summary():
    """
    Mendapatkan ringkasan status API untuk dashboard.
    
    Returns:
        Dict berisi ringkasan status API
    """
    try:
        # Ambil semua endpoint API yang aktif
        endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
        
        summary = {
            'total_endpoints': len(endpoints),
            'endpoints': [],
            'status_counts': {
                'up': 0,
                'down': 0,
                'error': 0,
                'timeout': 0,
                'unknown': 0
            },
            'last_updated': timezone.now()
        }
        
        # Ambil data untuk setiap endpoint
        for endpoint in endpoints:
            endpoint_data = {
                'name': endpoint.name,
                'url': endpoint.url,
                'priority': endpoint.priority,
                'paths': []
            }
            
            # Ambil monitor untuk setiap path
            monitors = APIMonitor.objects.filter(endpoint=endpoint)
            
            for monitor in monitors:
                path_data = {
                    'path': monitor.endpoint_path,
                    'status': monitor.status,
                    'response_time': monitor.response_time,
                    'last_checked': monitor.last_checked,
                    'error_message': monitor.error_message
                }
                
                endpoint_data['paths'].append(path_data)
                
                # Update status counts
                summary['status_counts'][monitor.status] = summary['status_counts'].get(monitor.status, 0) + 1
            
            summary['endpoints'].append(endpoint_data)
        
        return summary
    
    except Exception as e:
        logger.error(f"Error saat mendapatkan ringkasan status API: {e}")
        return {
            'error': str(e),
            'total_endpoints': 0,
            'endpoints': [],
            'status_counts': {},
            'last_updated': timezone.now()
        }