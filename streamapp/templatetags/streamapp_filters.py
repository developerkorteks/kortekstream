from django import template
from django.utils.safestring import mark_safe
from django.core.cache import cache
import re
from ..models import SiteConfiguration
import logging

register = template.Library()
logger = logging.getLogger(__name__)

# Cache untuk menyimpan domain sumber data
SOURCE_DOMAIN_CACHE_KEY = 'template_filter_source_domain'
DEFAULT_SOURCE_DOMAIN = 'v1.samehadaku.how'

def get_source_domain_from_cache():
    """
    Mendapatkan domain sumber data dari cache.
    Jika tidak ada di cache, gunakan nilai default.
    """
    # Coba ambil dari cache terlebih dahulu
    source_domain = cache.get(SOURCE_DOMAIN_CACHE_KEY)
    
    # Jika tidak ada di cache, gunakan nilai default
    if source_domain is None:
        # Gunakan nilai default dan simpan ke cache
        source_domain = DEFAULT_SOURCE_DOMAIN
        try:
            # Coba ambil dari database secara sinkron (hanya saat server startup)
            # Ini hanya dijalankan sekali saat cache kosong
            db_domain = SiteConfiguration.get_config('SOURCE_DOMAIN')
            if db_domain:
                source_domain = db_domain
        except Exception as e:
            logger.error(f"Error getting SOURCE_DOMAIN from database: {e}")
        
        # Simpan ke cache untuk digunakan selanjutnya
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

@register.simple_tag
def get_site_config(key, default=""):
    """
    Mendapatkan nilai konfigurasi situs berdasarkan key.
    Menggunakan cache untuk menghindari operasi database.
    """
    cache_key = f'template_tag_site_config_{key}'
    
    # Coba ambil dari cache terlebih dahulu
    value = cache.get(cache_key)
    
    # Jika tidak ada di cache, coba ambil dari database
    if value is None:
        try:
            value = SiteConfiguration.get_config(key, default)
            # Simpan ke cache untuk digunakan selanjutnya
            cache.set(cache_key, value, 60*60*24)  # Cache selama 24 jam
        except Exception as e:
            logger.error(f"Error getting site config for key {key}: {e}")
            value = default
    
    return value