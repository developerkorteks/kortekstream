#!/usr/bin/env python3
"""
Test script untuk memverifikasi sistem riwayat dinamis
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

from streamapp.models import APIEndpoint
from streamapp.utils import get_current_source_domain

def test_dynamic_api_system():
    """Test sistem API dinamis"""
    print("=== Testing Dynamic API System ===")
    
    # Test 1: Check current API endpoints
    print("\n1. Checking current API endpoints...")
    try:
        endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
        print(f"Found {endpoints.count()} active endpoints:")
        for endpoint in endpoints:
            print(f"  - {endpoint.name}: {endpoint.url} (domain: {endpoint.source_domain})")
    except Exception as e:
        print(f"Error getting endpoints: {e}")
    
    # Test 2: Check current source domain
    print("\n2. Checking current source domain...")
    try:
        current_domain = get_current_source_domain()
        print(f"Current source domain: {current_domain}")
    except Exception as e:
        print(f"Error getting current domain: {e}")
    
    # Test 3: Test URL building
    print("\n3. Testing URL building...")
    try:
        from streamapp.utils import build_dynamic_url
        test_path = "anime/one-piece/episode-1"
        dynamic_url = build_dynamic_url(test_path)
        print(f"Built URL for '{test_path}': {dynamic_url}")
    except Exception as e:
        print(f"Error building URL: {e}")
    
    print("\n=== Test completed ===")

def test_history_storage():
    """Test penyimpanan riwayat dengan API dinamis"""
    print("\n=== Testing History Storage ===")
    
    # Simulate history data with API source
    history_data = {
        "id": 12345,
        "title": "One Piece",
        "slug": "one-piece",
        "episodeSlug": "one-piece-episode-1",
        "episodeTitle": "Episode 1 - Saya Adalah Luffy!",
        "cover": "https://example.com/cover.jpg",
        "watchedAt": "2024-01-01T12:00:00Z",
        "apiSource": {
            "name": "Samehadaku API",
            "domain": "v1.samehadaku.how",
            "endpoint": "https://api.samehadaku.how/api/v1"
        }
    }
    
    print("Sample history data with API source:")
    print(f"  Title: {history_data['title']}")
    print(f"  Episode: {history_data['episodeTitle']}")
    print(f"  API Source: {history_data['apiSource']['name']}")
    print(f"  Domain: {history_data['apiSource']['domain']}")
    
    print("\n=== History storage test completed ===")

if __name__ == "__main__":
    test_dynamic_api_system()
    test_history_storage() 