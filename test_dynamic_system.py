#!/usr/bin/env python
"""
Test script untuk memverifikasi sistem dynamic berfungsi dengan baik.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from streamapp.utils import get_current_source_domain, build_dynamic_url, get_api_endpoint_info
from streamapp.models import APIEndpoint
import logging

logger = logging.getLogger(__name__)

def test_domain_functions():
    """Test fungsi domain management"""
    print("🧪 Testing domain functions...")
    
    try:
        # Test get_current_source_domain
        domain = get_current_source_domain()
        print(f"✅ Current source domain: {domain}")
        
        # Test build_dynamic_url
        url = build_dynamic_url("anime/one-piece/")
        print(f"✅ Dynamic URL built: {url}")
        
        # Test get_api_endpoint_info
        info = get_api_endpoint_info()
        print(f"✅ API endpoint info: {info['name']} ({info['url']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing domain functions: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🧪 Testing API endpoints...")
    
    try:
        endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
        print(f"✅ Found {endpoints.count()} active endpoints:")
        
        for endpoint in endpoints:
            print(f"  - {endpoint.name} ({endpoint.url}) - Priority: {endpoint.priority}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False

def test_async_functions():
    """Test async functions"""
    print("\n🧪 Testing async functions...")
    
    try:
        import asyncio
        from streamapp.utils import get_current_source_domain_async, build_dynamic_url_async
        
        async def test_async():
            # Test async domain function
            domain = await get_current_source_domain_async()
            print(f"✅ Async current source domain: {domain}")
            
            # Test async URL building
            url = await build_dynamic_url_async("anime/one-piece/")
            print(f"✅ Async dynamic URL built: {url}")
            
            return True
        
        # Run async test
        result = asyncio.run(test_async())
        return result
        
    except Exception as e:
        print(f"❌ Error testing async functions: {e}")
        return False

def test_template_filters():
    """Test template filters"""
    print("\n🧪 Testing template filters...")
    
    try:
        from streamapp.templatetags.streamapp_filters import (
            extract_anime_slug, 
            extract_episode_slug, 
            format_url,
            get_current_source_domain
        )
        
        # Test extract_anime_slug
        test_url = "https://v1.samehadaku.how/anime/one-piece/"
        anime_slug = extract_anime_slug(test_url)
        print(f"✅ Anime slug extracted: {anime_slug}")
        
        # Test extract_episode_slug
        test_episode_url = "https://v1.samehadaku.how/one-piece-episode-1/"
        episode_slug = extract_episode_slug(test_episode_url)
        print(f"✅ Episode slug extracted: {episode_slug}")
        
        # Test format_url
        test_image_path = "/wp-content/uploads/image.jpg"
        formatted_url = format_url(test_image_path)
        print(f"✅ Image URL formatted: {formatted_url}")
        
        # Test get_current_source_domain
        current_domain = get_current_source_domain()
        print(f"✅ Current source domain (template): {current_domain}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing template filters: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Dynamic System...")
    print("="*50)
    
    tests = [
        ("Domain Functions", test_domain_functions),
        ("API Endpoints", test_api_endpoints),
        ("Async Functions", test_async_functions),
        ("Template Filters", test_template_filters),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Dynamic system is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 