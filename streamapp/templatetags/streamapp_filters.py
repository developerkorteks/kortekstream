from django import template
from django.utils.safestring import mark_safe
from django.core.cache import cache
import re
from ..models import SiteConfiguration
import logging
from asgiref.sync import sync_to_async

register = template.Library()
logger = logging.getLogger(__name__)

# Cache untuk menyimpan domain sumber data
SOURCE_DOMAIN_CACHE_KEY = 'template_filter_source_domain'
DEFAULT_SOURCE_DOMAIN = 'v1.samehadaku.how'

def get_source_domain_from_cache():
    """
    Mendapatkan domain sumber data dari cache atau database secara synchronous.
    """
    source_domain = cache.get(SOURCE_DOMAIN_CACHE_KEY)
    if source_domain is None:
        source_domain = AsyncToSync(SiteConfiguration.get_current_source_domain)()
        cache.set(SOURCE_DOMAIN_CACHE_KEY, source_domain, 60*60*24)  # Cache selama 24 jam
    return source_domain

@register.filter
def extract_anime_slug(url):
    """
    Ekstrak anime slug dari URL.
    Contoh: https://domain.com/anime/one-piece/ -> one-piece
    """
    if not url:
        return ""
    
    # Dapatkan domain sumber data dari cache
    source_domain = get_source_domain_from_cache()
    
    # Pastikan source_domain adalah string
    if source_domain is not None:
        source_domain = str(source_domain)
    else:
        source_domain = DEFAULT_SOURCE_DOMAIN
    
    # Hapus protokol dan domain dari URL
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^' + re.escape(source_domain), '', url)
    
    # Hapus 'anime/' dari URL
    url = re.sub(r'^/?anime/', '', url)
    
    # Hapus trailing slash
    url = url.rstrip('/')
    
    return url

@register.filter
def extract_episode_slug(url):
    """
    Ekstrak episode slug dari URL.
    Contoh: https://domain.com/one-piece-episode-1/ -> one-piece-episode-1
    """
    if not url:
        return ""
    
    # Dapatkan domain sumber data dari cache
    source_domain = get_source_domain_from_cache()
    
    # Pastikan source_domain adalah string
    if source_domain is not None:
        source_domain = str(source_domain)
    else:
        source_domain = DEFAULT_SOURCE_DOMAIN
    
    # Hapus protokol dan domain dari URL
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^' + re.escape(source_domain), '', url)
    
    # Hapus trailing slash
    url = url.rstrip('/')
    
    # Hapus leading slash
    url = url.lstrip('/')
    
    return url

@register.filter
def format_url(url):
    """
    Memformat URL dengan domain sumber yang benar.
    Contoh: /path/to/image.jpg -> https://domain.com/path/to/image.jpg
    """
    if not url:
        return ""
    
    # Jika URL sudah memiliki protokol, kembalikan apa adanya
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    # Dapatkan domain sumber data
    source_domain = get_source_domain_from_cache()
    
    # Pastikan source_domain adalah string
    if source_domain is not None:
        source_domain = str(source_domain)
    else:
        source_domain = DEFAULT_SOURCE_DOMAIN
    
    # Pastikan URL tidak dimulai dengan // jika dimulai dengan /
    if url.startswith('/'):
        url = url[1:]
    
    # Format URL dengan domain sumber
    formatted_url = f'https://{source_domain}/{url}'
    
    return formatted_url

@register.simple_tag
def get_site_config(key, default=""):
    """
    Mendapatkan nilai konfigurasi situs berdasarkan key secara synchronous.
    Menggunakan cache untuk menghindari operasi database.
    """
    cache_key = f'template_tag_site_config_{key}'
    
    # Coba ambil dari cache terlebih dahulu
    value = cache.get(cache_key)
    
    # Jika tidak ada di cache, coba ambil dari database
    if value is None:
        try:
            value = AsyncToSync(SiteConfiguration.get_config)(key, default)
            # Simpan ke cache untuk digunakan selanjutnya
            cache.set(cache_key, value, 60*60*24)  # Cache selama 24 jam
        except Exception as e:
            logger.error(f"Error getting site config for key {key}: {e}")
            value = default
    
    return value

@register.simple_tag
def get_current_source_domain():
    """
    Mendapatkan domain sumber data yang sedang aktif secara synchronous.
    """
    return get_source_domain_from_cache()