#!/usr/bin/env python3
"""
Script untuk monitoring sistem fallback API secara realtime.
Memantau status endpoint dan performa fallback.
"""

import os
import sys
import django
import time
import logging
from datetime import datetime, timedelta
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

class FallbackSystemMonitor:
    """
    Class untuk monitoring sistem fallback API secara realtime.
    """
    
    def __init__(self):
        self.client = FallbackAPIClient()
        self.monitoring_data = []
    
    def get_endpoint_status(self):
        """Dapatkan status semua endpoint."""
        print("📊 Endpoint Status Report")
        print("=" * 50)
        
        endpoints = APIEndpoint.objects.all().order_by('-priority')
        
        if not endpoints:
            print("❌ Tidak ada endpoint yang dikonfigurasi")
            return
        
        for endpoint in endpoints:
            status = "🟢 ACTIVE" if endpoint.is_active else "🔴 INACTIVE"
            last_used = endpoint.last_used.strftime("%Y-%m-%d %H:%M:%S") if endpoint.last_used else "Never"
            
            print(f"\n📡 {endpoint.name}")
            print(f"   URL: {endpoint.url}")
            print(f"   Domain: {endpoint.source_domain}")
            print(f"   Priority: {endpoint.priority}")
            print(f"   Status: {status}")
            print(f"   Success Count: {endpoint.success_count}")
            print(f"   Last Used: {last_used}")
            
            # Health check
            if endpoint.is_active:
                health_status = "🟢 UP" if check_endpoint_health(endpoint) else "🔴 DOWN"
                print(f"   Health: {health_status}")
    
    def get_fallback_chain(self):
        """Tampilkan chain fallback yang aktif."""
        print("\n🔄 Fallback Chain")
        print("=" * 50)
        
        active_endpoints = get_api_endpoints()
        
        if not active_endpoints:
            print("❌ Tidak ada endpoint aktif")
            return
        
        for i, endpoint in enumerate(active_endpoints):
            position = "🥇 PRIMARY" if i == 0 else f"🥈 BACKUP {i}"
            print(f"\n{position}: {endpoint.name}")
            print(f"   URL: {endpoint.url}")
            print(f"   Domain: {endpoint.source_domain}")
            print(f"   Priority: {endpoint.priority}")
    
    def get_cache_status(self):
        """Tampilkan status cache."""
        print("\n💾 Cache Status")
        print("=" * 50)
        
        cache_keys = [
            "api_endpoints",
            "template_filter_source_domain",
            "current_source_domain"
        ]
        
        for key in cache_keys:
            value = cache.get(key)
            status = "✅ CACHED" if value is not None else "❌ NOT CACHED"
            print(f"{key}: {status}")
    
    def get_api_monitor_stats(self):
        """Tampilkan statistik API monitor."""
        print("\n📈 API Monitor Statistics")
        print("=" * 50)
        
        # Get recent monitors (last 24 hours)
        yesterday = timezone.now() - timedelta(days=1)
        recent_monitors = APIMonitor.objects.filter(last_checked__gte=yesterday)
        
        if not recent_monitors:
            print("❌ Tidak ada data monitoring dalam 24 jam terakhir")
            return
        
        # Group by status
        status_counts = {}
        for monitor in recent_monitors:
            status = monitor.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("Status distribution (last 24 hours):")
        for status, count in status_counts.items():
            emoji = "🟢" if status == "up" else "🔴" if status == "down" else "🟡"
            print(f"   {emoji} {status.upper()}: {count}")
        
        # Average response time
        successful_monitors = recent_monitors.filter(response_time__isnull=False)
        if successful_monitors:
            avg_response_time = sum(m.response_time for m in successful_monitors) / len(successful_monitors)
            print(f"\n📊 Average Response Time: {avg_response_time:.2f}ms")
    
    def test_fallback_scenario(self):
        """Test skenario fallback."""
        print("\n🧪 Testing Fallback Scenario")
        print("=" * 50)
        
        # Refresh client
        self.client.refresh_endpoints()
        
        if not self.client.endpoints:
            print("❌ Tidak ada endpoint untuk testing")
            return
        
        print(f"✅ Loaded {len(self.client.endpoints)} endpoints")
        print(f"🎯 Current endpoint: {self.client.get_current_endpoint().name}")
        
        # Test fallback
        try:
            # Simulate failure and fallback
            old_index = self.client.current_endpoint_index
            success = self.client._fallback_to_next_endpoint()
            
            if success:
                new_endpoint = self.client.get_current_endpoint()
                print(f"✅ Fallback successful: {new_endpoint.name}")
            else:
                print("❌ Fallback failed - no more endpoints available")
                
        except Exception as e:
            print(f"❌ Error during fallback test: {e}")
    
    def monitor_realtime(self, duration_minutes=5):
        """Monitor sistem secara realtime."""
        print(f"\n⏱️  Starting realtime monitoring for {duration_minutes} minutes...")
        print("=" * 50)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Get current endpoint
            self.client.refresh_endpoints()
            current_endpoint = self.client.get_current_endpoint()
            
            if current_endpoint:
                print(f"[{current_time}] 🎯 Using: {current_endpoint.name}")
                
                # Check health
                if check_endpoint_health(current_endpoint):
                    print(f"[{current_time}] 🟢 Health: OK")
                else:
                    print(f"[{current_time}] 🔴 Health: FAILED")
            else:
                print(f"[{current_time}] ❌ No active endpoint")
            
            # Wait 10 seconds
            time.sleep(10)
        
        print("\n✅ Realtime monitoring completed")
    
    def run_full_monitoring(self):
        """Jalankan monitoring lengkap."""
        print("🚀 Starting Fallback System Monitoring...")
        print("=" * 60)
        
        # Run all monitoring functions
        self.get_endpoint_status()
        self.get_fallback_chain()
        self.get_cache_status()
        self.get_api_monitor_stats()
        self.test_fallback_scenario()
        
        # Ask for realtime monitoring
        print("\n" + "=" * 60)
        response = input("Do you want to start realtime monitoring? (y/n): ")
        
        if response.lower() == 'y':
            duration = input("Enter monitoring duration in minutes (default 5): ")
            try:
                duration = int(duration) if duration else 5
                self.monitor_realtime(duration)
            except ValueError:
                print("Invalid duration, using default 5 minutes")
                self.monitor_realtime(5)

def main():
    """Main function."""
    monitor = FallbackSystemMonitor()
    monitor.run_full_monitoring()

if __name__ == "__main__":
    main() 