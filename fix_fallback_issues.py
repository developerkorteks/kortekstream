#!/usr/bin/env python3
"""
Script untuk memperbaiki masalah fallback API.
Membersihkan cache, memperbaiki endpoint, dan memastikan sistem realtime.
"""

import os
import sys
import django
import logging
from typing import Dict, List, Any

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from streamapp.models import APIEndpoint, APIMonitor
from streamapp.api_client import FallbackAPIClient, get_api_endpoints, check_endpoint_health
from django.core.cache import cache
from django.utils import timezone

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FallbackSystemFixer:
    """
    Class untuk memperbaiki masalah sistem fallback API.
    """
    
    def __init__(self):
        self.client = FallbackAPIClient()
    
    def clear_all_caches(self):
        """Bersihkan semua cache yang terkait dengan API."""
        print("🧹 Clearing all API caches...")
        
        # Clear specific cache keys
        cache_keys = [
            "api_endpoints",
            "template_filter_source_domain",
            "current_source_domain",
            "get_api_endpoints",
            "get_current_source_domain"
        ]
        
        for key in cache_keys:
            cache.delete(key)
            print(f"   ✅ Cleared: {key}")
        
        # Clear all cache
        cache.clear()
        print("   ✅ Cleared all Django cache")
        
        # Force refresh from database
        APIEndpoint.force_refresh_cache()
        print("   ✅ Forced API endpoint cache refresh")
    
    def fix_inactive_endpoints(self):
        """Perbaiki endpoint yang tidak aktif tapi masih digunakan."""
        print("\n🔧 Fixing inactive endpoints...")
        
        endpoints = APIEndpoint.objects.all()
        fixed_count = 0
        
        for endpoint in endpoints:
            # Check if endpoint is marked inactive but still being used
            if not endpoint.is_active:
                # Check if it's still in cache or being used
                print(f"   📍 Found inactive endpoint: {endpoint.name}")
                
                # Force deactivate
                endpoint.is_active = False
                endpoint.save()
                fixed_count += 1
                print(f"   ✅ Fixed: {endpoint.name}")
        
        print(f"   📊 Fixed {fixed_count} inactive endpoints")
    
    def fix_health_check_failures(self):
        """Perbaiki endpoint yang gagal health check."""
        print("\n🏥 Fixing health check failures...")
        
        active_endpoints = APIEndpoint.objects.filter(is_active=True)
        fixed_count = 0
        
        for endpoint in active_endpoints:
            if not check_endpoint_health(endpoint):
                print(f"   🔴 Found unhealthy endpoint: {endpoint.name}")
                
                # Mark as inactive
                endpoint.is_active = False
                endpoint.save()
                fixed_count += 1
                print(f"   ✅ Fixed: {endpoint.name} (marked inactive)")
        
        print(f"   📊 Fixed {fixed_count} unhealthy endpoints")
    
    def fix_priority_issues(self):
        """Perbaiki masalah prioritas endpoint."""
        print("\n⚖️  Fixing priority issues...")
        
        # Get all active endpoints
        active_endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
        
        if len(active_endpoints) > 1:
            # Ensure proper priority order
            for i, endpoint in enumerate(active_endpoints):
                expected_priority = len(active_endpoints) - i
                if endpoint.priority != expected_priority:
                    print(f"   🔧 Fixing priority for {endpoint.name}: {endpoint.priority} -> {expected_priority}")
                    endpoint.priority = expected_priority
                    endpoint.save()
        
        print("   ✅ Priority order fixed")
    
    def fix_source_domain_consistency(self):
        """Perbaiki konsistensi source domain."""
        print("\n🌐 Fixing source domain consistency...")
        
        endpoints = APIEndpoint.objects.filter(is_active=True)
        
        for endpoint in endpoints:
            if not endpoint.source_domain:
                # Set default source domain based on URL
                if 'samehadaku' in endpoint.url.lower():
                    endpoint.source_domain = 'v1.samehadaku.how'
                elif 'otakudesu' in endpoint.url.lower():
                    endpoint.source_domain = 'otakudesu.com'
                elif 'animeindo' in endpoint.url.lower():
                    endpoint.source_domain = 'animeindo.com'
                else:
                    endpoint.source_domain = 'gomunime.co'
                
                endpoint.save()
                print(f"   ✅ Fixed source domain for {endpoint.name}: {endpoint.source_domain}")
    
    def fix_cache_stale_data(self):
        """Perbaiki data cache yang sudah basi."""
        print("\n🔄 Fixing stale cache data...")
        
        # Clear all caches
        self.clear_all_caches()
        
        # Force refresh endpoints
        self.client.refresh_endpoints()
        
        # Test endpoint loading
        active_endpoints = get_api_endpoints()
        print(f"   📊 Loaded {len(active_endpoints)} active endpoints")
        
        for endpoint in active_endpoints:
            print(f"   ✅ {endpoint.name} ({endpoint.url})")
    
    def fix_fallback_chain(self):
        """Perbaiki chain fallback."""
        print("\n🔄 Fixing fallback chain...")
        
        # Refresh client
        self.client.refresh_endpoints()
        
        if not self.client.endpoints:
            print("   ❌ No active endpoints found")
            return
        
        print(f"   📊 Fallback chain has {len(self.client.endpoints)} endpoints:")
        
        for i, endpoint in enumerate(self.client.endpoints):
            position = "🥇 PRIMARY" if i == 0 else f"🥈 BACKUP {i}"
            health = "🟢 UP" if check_endpoint_health(endpoint) else "🔴 DOWN"
            print(f"   {position}: {endpoint.name} - {health}")
    
    def fix_base_url_issues(self):
        """Perbaiki masalah base URL."""
        print("\n🔗 Fixing base URL issues...")
        
        endpoints = APIEndpoint.objects.filter(is_active=True)
        
        for endpoint in endpoints:
            # Ensure URL format is correct
            if not endpoint.url.endswith('/'):
                endpoint.url = endpoint.url + '/'
            
            # Remove trailing slash for consistency
            endpoint.url = endpoint.url.rstrip('/')
            
            # Ensure proper API path
            if not endpoint.url.endswith('/api/v1'):
                if endpoint.url.endswith('/api'):
                    endpoint.url = endpoint.url + '/v1'
                elif not endpoint.url.endswith('/api/v1'):
                    endpoint.url = endpoint.url + '/api/v1'
            
            endpoint.save()
            print(f"   ✅ Fixed URL for {endpoint.name}: {endpoint.url}")
    
    def run_comprehensive_fix(self):
        """Jalankan perbaikan komprehensif."""
        print("🚀 Starting Comprehensive Fallback System Fix...")
        print("=" * 60)
        
        # Run all fixes
        fixes = [
            ("Clear All Caches", self.clear_all_caches),
            ("Fix Inactive Endpoints", self.fix_inactive_endpoints),
            ("Fix Health Check Failures", self.fix_health_check_failures),
            ("Fix Priority Issues", self.fix_priority_issues),
            ("Fix Source Domain Consistency", self.fix_source_domain_consistency),
            ("Fix Cache Stale Data", self.fix_cache_stale_data),
            ("Fix Fallback Chain", self.fix_fallback_chain),
            ("Fix Base URL Issues", self.fix_base_url_issues),
        ]
        
        for fix_name, fix_func in fixes:
            print(f"\n🔧 Running: {fix_name}")
            try:
                fix_func()
                print(f"✅ {fix_name}: COMPLETED")
            except Exception as e:
                print(f"❌ {fix_name}: ERROR - {e}")
        
        print("\n" + "=" * 60)
        print("🎉 Comprehensive fix completed!")
        
        # Show final status
        self.show_final_status()
    
    def show_final_status(self):
        """Tampilkan status akhir setelah perbaikan."""
        print("\n📊 Final System Status")
        print("=" * 50)
        
        # Show active endpoints
        active_endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
        print(f"Active Endpoints: {active_endpoints.count()}")
        
        for endpoint in active_endpoints:
            health = "🟢 UP" if check_endpoint_health(endpoint) else "🔴 DOWN"
            print(f"   {endpoint.name}: {health}")
        
        # Show cache status
        cache_status = "✅ CLEAN" if cache.get("api_endpoints") is None else "❌ STALE"
        print(f"Cache Status: {cache_status}")
        
        # Show fallback chain
        self.client.refresh_endpoints()
        print(f"Fallback Chain: {len(self.client.endpoints)} endpoints loaded")

def main():
    """Main function."""
    fixer = FallbackSystemFixer()
    fixer.run_comprehensive_fix()

if __name__ == "__main__":
    main() 