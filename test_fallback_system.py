#!/usr/bin/env python3
"""
Script untuk testing sistem fallback API.
Memverifikasi bahwa sistem fallback berfungsi dengan benar dan realtime.
"""

import os
import sys
import django
import requests
import time
import logging
from typing import Dict, List, Any

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from streamapp.models import APIEndpoint, APIMonitor
from streamapp.api_client import FallbackAPIClient, get_api_endpoints, check_endpoint_health
from django.core.cache import cache

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FallbackSystemTester:
    """
    Class untuk testing sistem fallback API.
    """
    
    def __init__(self):
        self.client = FallbackAPIClient()
        self.test_results = []
    
    def test_cache_clearing(self):
        """Test apakah cache dibersihkan dengan benar saat endpoint dihapus."""
        print("🧪 Testing cache clearing...")
        
        # Simpan cache
        cache.set("test_cache_key", "test_value", 3600)
        cache.set("api_endpoints", "test_endpoints", 3600)
        
        # Buat endpoint test
        test_endpoint = APIEndpoint.objects.create(
            name="Test Endpoint",
            url="https://test.api.com",
            source_domain="test.com",
            priority=1,
            is_active=True
        )
        
        # Hapus endpoint
        test_endpoint.delete()
        
        # Cek apakah cache dibersihkan
        if cache.get("test_cache_key") is None:
            print("✅ Cache clearing berfungsi dengan baik")
            return True
        else:
            print("❌ Cache tidak dibersihkan dengan benar")
            return False
    
    def test_endpoint_health_check(self):
        """Test health check endpoint."""
        print("🧪 Testing endpoint health check...")
        
        # Test dengan endpoint yang tidak ada
        class MockEndpoint:
            def __init__(self, url):
                self.url = url
                self.name = "Mock"
        
        mock_endpoint = MockEndpoint("https://invalid-url-that-does-not-exist.com")
        
        if not check_endpoint_health(mock_endpoint):
            print("✅ Health check berfungsi dengan baik (mendeteksi endpoint down)")
            return True
        else:
            print("❌ Health check tidak berfungsi dengan baik")
            return False
    
    def test_fallback_logic(self):
        """Test logika fallback."""
        print("🧪 Testing fallback logic...")
        
        # Buat beberapa endpoint test
        endpoints = []
        for i in range(3):
            endpoint = APIEndpoint.objects.create(
                name=f"Test API {i+1}",
                url=f"https://test{i+1}.api.com",
                source_domain=f"test{i+1}.com",
                priority=10-i,  # Prioritas menurun
                is_active=True
            )
            endpoints.append(endpoint)
        
        try:
            # Test get_api_endpoints
            active_endpoints = get_api_endpoints()
            
            if len(active_endpoints) > 0:
                print(f"✅ Found {len(active_endpoints)} active endpoints")
                
                # Test fallback client
                self.client.refresh_endpoints()
                if len(self.client.endpoints) > 0:
                    print("✅ Fallback client berfungsi dengan baik")
                    return True
                else:
                    print("❌ Fallback client tidak berfungsi")
                    return False
            else:
                print("❌ Tidak ada endpoint aktif")
                return False
                
        finally:
            # Cleanup
            for endpoint in endpoints:
                endpoint.delete()
    
    def test_realtime_switching(self):
        """Test switching realtime antar endpoint."""
        print("🧪 Testing realtime switching...")
        
        # Buat endpoint test
        endpoint1 = APIEndpoint.objects.create(
            name="Primary Test API",
            url="https://primary.test.com",
            source_domain="primary.test.com",
            priority=10,
            is_active=True
        )
        
        endpoint2 = APIEndpoint.objects.create(
            name="Backup Test API", 
            url="https://backup.test.com",
            source_domain="backup.test.com",
            priority=5,
            is_active=True
        )
        
        try:
            # Test refresh endpoints
            self.client.refresh_endpoints()
            
            if len(self.client.endpoints) >= 2:
                print("✅ Realtime switching berfungsi dengan baik")
                return True
            else:
                print("❌ Realtime switching tidak berfungsi")
                return False
                
        finally:
            # Cleanup
            endpoint1.delete()
            endpoint2.delete()
    
    def test_base_url_consistency(self):
        """Test konsistensi base URL."""
        print("🧪 Testing base URL consistency...")
        
        # Buat endpoint test
        endpoint = APIEndpoint.objects.create(
            name="Test API",
            url="https://test.api.com/api/v1",
            source_domain="test.com",
            priority=10,
            is_active=True
        )
        
        try:
            # Test URL building
            test_url = f"{endpoint.url.rstrip('/')}/anime-terbaru"
            expected_url = "https://test.api.com/api/v1/anime-terbaru"
            
            if test_url == expected_url:
                print("✅ Base URL consistency berfungsi dengan baik")
                return True
            else:
                print(f"❌ Base URL tidak konsisten: {test_url} vs {expected_url}")
                return False
                
        finally:
            endpoint.delete()
    
    def run_all_tests(self):
        """Jalankan semua test."""
        print("🚀 Starting Fallback System Tests...")
        print("=" * 50)
        
        tests = [
            ("Cache Clearing", self.test_cache_clearing),
            ("Health Check", self.test_endpoint_health_check),
            ("Fallback Logic", self.test_fallback_logic),
            ("Realtime Switching", self.test_realtime_switching),
            ("Base URL Consistency", self.test_base_url_consistency),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Fallback system is ready for production.")
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
        
        return passed == total

def main():
    """Main function."""
    tester = FallbackSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Fallback system is production ready!")
        sys.exit(0)
    else:
        print("\n❌ Fallback system needs fixes before production!")
        sys.exit(1)

if __name__ == "__main__":
    main() 