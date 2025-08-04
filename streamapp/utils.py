import re
import logging
from typing import Optional, Dict, Any
from django.core.cache import cache
from .models import APIEndpoint, SiteConfiguration
from asgiref.sync import AsyncToSync, sync_to_async
import asyncio

logger = logging.getLogger(__name__)

def get_current_source_domain() -> str:
    """
    Get the current active source domain from API endpoints or fallback to configuration.
    
    Returns:
        str: Current source domain
    """
    try:
        # Try to get from active API endpoint first
        active_endpoint = APIEndpoint.objects.filter(is_active=True).order_by('-priority').first()
        if active_endpoint and active_endpoint.source_domain:
            return active_endpoint.source_domain
    except Exception as e:
        logger.error(f"Error getting source domain from API endpoint: {e}")
    
    # Fallback to SiteConfiguration
    try:
        # Use sync version for sync context
        return SiteConfiguration.get_current_source_domain_sync()
    except Exception as e:
        logger.error(f"Error getting source domain from SiteConfiguration: {e}")
        return "gomunime.co"  # Final fallback

async def get_current_source_domain_async() -> str:
    """
    Get current source domain asynchronously.
    
    Returns:
        str: Current source domain
    """
    try:
        from .models import APIEndpoint, SiteConfiguration
        from asgiref.sync import sync_to_async
        
        # Try to get from APIEndpoint first
        try:
            active_endpoint = await sync_to_async(APIEndpoint.objects.filter)(is_active=True)
            active_endpoint = await sync_to_async(active_endpoint.order_by)('-priority')
            active_endpoint = await sync_to_async(active_endpoint.first)()
            
            if active_endpoint and active_endpoint.source_domain:
                return active_endpoint.source_domain
        except Exception as e:
            logger.error(f"Error getting source domain from API endpoint: {e}")
        
        # Fallback to SiteConfiguration
        try:
            config = await sync_to_async(SiteConfiguration.objects.get)(key='SOURCE_DOMAIN', is_active=True)
            return config.value
        except SiteConfiguration.DoesNotExist:
            logger.warning("SOURCE_DOMAIN configuration not found")
        except Exception as e:
            logger.error(f"Error getting source domain from SiteConfiguration: {e}")
        
        # Final fallback
        return "gomunime.co"
        
    except Exception as e:
        logger.error(f"Error in get_current_source_domain_async: {e}")
        return "gomunime.co"

def build_dynamic_url(path: str, domain: Optional[str] = None) -> str:
    """
    Build a dynamic URL using the current source domain.
    
    Args:
        path: URL path (e.g., 'anime/one-piece/')
        domain: Optional domain override
        
    Returns:
        str: Complete URL with domain
    """
    if not domain:
        domain = get_current_source_domain()
    
    # Ensure domain doesn't have protocol
    domain = re.sub(r'^https?://', '', domain)
    
    # Ensure path doesn't start with slash
    path = path.lstrip('/')
    
    return f"https://{domain}/{path}"

async def build_dynamic_url_async(path: str, domain: Optional[str] = None) -> str:
    """
    Async version of build_dynamic_url.
    
    Args:
        path: URL path (e.g., 'anime/one-piece/')
        domain: Optional domain override
        
    Returns:
        str: Complete URL with domain
    """
    if not domain:
        domain = await get_current_source_domain_async()
    
    # Ensure domain doesn't have protocol
    domain = re.sub(r'^https?://', '', domain)
    
    # Ensure path doesn't start with slash
    path = path.lstrip('/')
    
    return f"https://{domain}/{path}"

def extract_anime_slug_from_url(url: str, domain: Optional[str] = None) -> str:
    """
    Extract anime slug from URL using dynamic domain.
    
    Args:
        url: Full URL
        domain: Optional domain override
        
    Returns:
        str: Anime slug
    """
    if not url:
        return ""
    
    if not domain:
        domain = get_current_source_domain()
    
    # Remove protocol and domain from URL
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^' + re.escape(domain), '', url)
    
    # Remove 'anime/' from URL
    url = re.sub(r'^/?anime/', '', url)
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    return url

def extract_episode_slug_from_url(url: str, domain: Optional[str] = None) -> str:
    """
    Extract episode slug from URL using dynamic domain.
    
    Args:
        url: Full URL
        domain: Optional domain override
        
    Returns:
        str: Episode slug
    """
    if not url:
        return ""
    
    if not domain:
        domain = get_current_source_domain()
    
    # Remove protocol and domain from URL
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^' + re.escape(domain), '', url)
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    # Remove leading slash
    url = url.lstrip('/')
    
    return url

def format_image_url(image_path: str, domain: Optional[str] = None) -> str:
    """
    Format image URL with dynamic domain.
    
    Args:
        image_path: Image path or URL
        domain: Optional domain override
        
    Returns:
        str: Complete image URL
    """
    if not image_path:
        return ""
    
    # If URL already has protocol, return as is
    if image_path.startswith('http://') or image_path.startswith('https://'):
        return image_path
    
    if not domain:
        domain = get_current_source_domain()
    
    # Ensure domain doesn't have protocol
    domain = re.sub(r'^https?://', '', domain)
    
    # Ensure image_path doesn't start with slash
    image_path = image_path.lstrip('/')
    
    return f"https://{domain}/{image_path}"

def get_api_endpoint_info() -> Dict[str, Any]:
    """
    Get information about the current active API endpoint.
    
    Returns:
        Dict containing endpoint information
    """
    try:
        active_endpoint = APIEndpoint.objects.filter(is_active=True).order_by('-priority').first()
        if active_endpoint:
            return {
                'name': active_endpoint.name,
                'url': active_endpoint.url,
                'source_domain': active_endpoint.source_domain,
                'priority': active_endpoint.priority,
                'success_count': active_endpoint.success_count,
                'is_active': active_endpoint.is_active
            }
    except Exception as e:
        logger.error(f"Error getting API endpoint info: {e}")
    
    return {
        'name': 'Default',
        'url': 'http://localhost:8001/api/v1',
        'source_domain': get_current_source_domain(),
        'priority': 0,
        'success_count': 0,
        'is_active': True
    }

def clear_domain_cache():
    """
    Clear all domain-related caches.
    """
    cache.delete('template_filter_source_domain')
    cache.delete('api_endpoints')
    logger.info("Domain cache cleared")

def validate_domain_format(domain: str) -> bool:
    """
    Validate domain format.
    
    Args:
        domain: Domain to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not domain:
        return False
    
    # Remove protocol if present
    domain = re.sub(r'^https?://', '', domain)
    
    # Basic domain validation
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    return bool(re.match(domain_pattern, domain)) 