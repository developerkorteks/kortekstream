import time
from typing import Any, Callable, Dict, Optional, TypeVar

from .config import settings

T = TypeVar("T")

# Simple in-memory cache
cache: Dict[str, Dict[str, Any]] = {}


def get_from_cache_or_fetch(
    key: str, 
    fetch_func: Callable[..., T], 
    *args, 
    ttl: Optional[int] = None, 
    **kwargs
) -> T:
    """
    Get data from cache or fetch it using the provided function.
    
    Args:
        key: Cache key
        fetch_func: Function to fetch data if not in cache
        ttl: Time to live in seconds (optional, defaults to settings.CACHE_TTL)
        *args, **kwargs: Arguments to pass to fetch_func
        
    Returns:
        Data from cache or from fetch_func
    """
    current_time = time.time()
    cache_ttl = ttl if ttl is not None else settings.CACHE_TTL
    
    if key in cache and (current_time - cache[key]["timestamp"]) < cache_ttl:
        print(f"CACHE HIT: Mengambil data dari cache untuk key: {key}")
        return cache[key]["data"]
    
    print(f"CACHE MISS: Melakukan fetch baru untuk key: {key}")
    try:
        data = fetch_func(*args, **kwargs)
        if data is not None:
            cache[key] = {"timestamp": current_time, "data": data}
        return data
    except Exception as e:
        print(f"Error saat fetching {key}: {e}")
        raise


def invalidate_cache(key: Optional[str] = None) -> None:
    """
    Invalidate cache for a specific key or all cache.
    
    Args:
        key: Cache key to invalidate (optional, if None, invalidate all cache)
    """
    global cache
    if key is None:
        cache = {}
        print("Semua cache telah diinvalidasi")
    elif key in cache:
        del cache[key]
        print(f"Cache untuk key {key} telah diinvalidasi")
    else:
        print(f"Cache untuk key {key} tidak ditemukan")


def get_cache_keys() -> list:
    """
    Get all cache keys.
    
    Returns:
        List of cache keys
    """
    return list(cache.keys())


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    stats = {
        "total_keys": len(cache),
        "keys": [],
    }
    
    current_time = time.time()
    for key, value in cache.items():
        age = current_time - value["timestamp"]
        stats["keys"].append({
            "key": key,
            "age": age,
            "size": len(str(value["data"])),
        })
    
    return stats