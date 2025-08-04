from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.utils import timezone
from streamapp.models import APIEndpoint, APIMonitor
from streamapp.api_client import FallbackAPIClient, get_api_endpoints, check_endpoint_health
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix fallback system issues and ensure realtime operation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear all API-related caches'
        )
        parser.add_argument(
            '--fix-endpoints',
            action='store_true',
            help='Fix inactive endpoints and health issues'
        )
        parser.add_argument(
            '--test-fallback',
            action='store_true',
            help='Test fallback system'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all fixes'
        )

    def handle(self, *args, **options):
        if options['all'] or not any([options['clear_cache'], options['fix_endpoints'], options['test_fallback']]):
            self.run_all_fixes()
        else:
            if options['clear_cache']:
                self.clear_all_caches()
            if options['fix_endpoints']:
                self.fix_endpoints()
            if options['test_fallback']:
                self.test_fallback_system()

    def clear_all_caches(self):
        """Clear all API-related caches."""
        self.stdout.write("🧹 Clearing all API caches...")
        
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
            self.stdout.write(f"   ✅ Cleared: {key}")
        
        # Clear all cache
        cache.clear()
        self.stdout.write("   ✅ Cleared all Django cache")
        
        # Force refresh from database
        APIEndpoint.force_refresh_cache()
        self.stdout.write("   ✅ Forced API endpoint cache refresh")

    def fix_endpoints(self):
        """Fix endpoint issues."""
        self.stdout.write("\n🔧 Fixing endpoint issues...")
        
        # Fix inactive endpoints
        endpoints = APIEndpoint.objects.all()
        fixed_count = 0
        
        for endpoint in endpoints:
            if not endpoint.is_active:
                self.stdout.write(f"   📍 Found inactive endpoint: {endpoint.name}")
                endpoint.is_active = False
                endpoint.save()
                fixed_count += 1
                self.stdout.write(f"   ✅ Fixed: {endpoint.name}")
        
        # Fix health check failures
        active_endpoints = APIEndpoint.objects.filter(is_active=True)
        health_fixed = 0
        
        for endpoint in active_endpoints:
            if not check_endpoint_health(endpoint):
                self.stdout.write(f"   🔴 Found unhealthy endpoint: {endpoint.name}")
                endpoint.is_active = False
                endpoint.save()
                health_fixed += 1
                self.stdout.write(f"   ✅ Fixed: {endpoint.name} (marked inactive)")
        
        self.stdout.write(f"   📊 Fixed {fixed_count} inactive endpoints")
        self.stdout.write(f"   📊 Fixed {health_fixed} unhealthy endpoints")

    def test_fallback_system(self):
        """Test fallback system."""
        self.stdout.write("\n🧪 Testing fallback system...")
        
        # Test endpoint loading
        active_endpoints = get_api_endpoints()
        self.stdout.write(f"   📊 Loaded {len(active_endpoints)} active endpoints")
        
        for endpoint in active_endpoints:
            health = "🟢 UP" if check_endpoint_health(endpoint) else "🔴 DOWN"
            self.stdout.write(f"   {endpoint.name}: {health}")
        
        # Test fallback client
        client = FallbackAPIClient()
        client.refresh_endpoints()
        
        if client.endpoints:
            self.stdout.write(f"   ✅ Fallback client loaded {len(client.endpoints)} endpoints")
            current = client.get_current_endpoint()
            if current:
                self.stdout.write(f"   🎯 Current endpoint: {current.name}")
        else:
            self.stdout.write("   ❌ No endpoints available for fallback")

    def run_all_fixes(self):
        """Run all fixes."""
        self.stdout.write("🚀 Starting Comprehensive Fallback System Fix...")
        self.stdout.write("=" * 60)
        
        # Clear caches
        self.clear_all_caches()
        
        # Fix endpoints
        self.fix_endpoints()
        
        # Test fallback
        self.test_fallback_system()
        
        # Show final status
        self.show_final_status()
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🎉 Comprehensive fix completed!")

    def show_final_status(self):
        """Show final system status."""
        self.stdout.write("\n📊 Final System Status")
        self.stdout.write("=" * 50)
        
        # Show active endpoints
        active_endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
        self.stdout.write(f"Active Endpoints: {active_endpoints.count()}")
        
        for endpoint in active_endpoints:
            health = "🟢 UP" if check_endpoint_health(endpoint) else "🔴 DOWN"
            self.stdout.write(f"   {endpoint.name}: {health}")
        
        # Show cache status
        cache_status = "✅ CLEAN" if cache.get("api_endpoints") is None else "❌ STALE"
        self.stdout.write(f"Cache Status: {cache_status}")
        
        # Show fallback chain
        client = FallbackAPIClient()
        client.refresh_endpoints()
        self.stdout.write(f"Fallback Chain: {len(client.endpoints)} endpoints loaded") 