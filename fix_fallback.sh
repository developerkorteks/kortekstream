#!/bin/bash

# Script untuk memperbaiki sistem fallback API
# Pastikan virtual environment aktif dan Django terinstall

echo "🚀 Starting Fallback System Fix..."

# Aktifkan virtual environment
source venv/bin/activate

# Clear all caches
echo "🧹 Clearing all caches..."
python manage.py shell -c "
from django.core.cache import cache
from streamapp.models import APIEndpoint

# Clear specific cache keys
cache_keys = [
    'api_endpoints',
    'template_filter_source_domain', 
    'current_source_domain',
    'get_api_endpoints',
    'get_current_source_domain'
]

for key in cache_keys:
    cache.delete(key)
    print(f'✅ Cleared: {key}')

# Clear all cache
cache.clear()
print('✅ Cleared all Django cache')

# Force refresh from database
APIEndpoint.force_refresh_cache()
print('✅ Forced API endpoint cache refresh')
"

# Fix endpoint issues
echo "🔧 Fixing endpoint issues..."
python manage.py shell -c "
from streamapp.models import APIEndpoint
from streamapp.api_client import check_endpoint_health

# Fix inactive endpoints
endpoints = APIEndpoint.objects.all()
fixed_count = 0

for endpoint in endpoints:
    if not endpoint.is_active:
        print(f'📍 Found inactive endpoint: {endpoint.name}')
        endpoint.is_active = False
        endpoint.save()
        fixed_count += 1
        print(f'✅ Fixed: {endpoint.name}')

# Fix health check failures
active_endpoints = APIEndpoint.objects.filter(is_active=True)
health_fixed = 0

for endpoint in active_endpoints:
    if not check_endpoint_health(endpoint):
        print(f'🔴 Found unhealthy endpoint: {endpoint.name}')
        endpoint.is_active = False
        endpoint.save()
        health_fixed += 1
        print(f'✅ Fixed: {endpoint.name} (marked inactive)')

print(f'📊 Fixed {fixed_count} inactive endpoints')
print(f'📊 Fixed {health_fixed} unhealthy endpoints')
"

# Test fallback system
echo "🧪 Testing fallback system..."
python manage.py shell -c "
from streamapp.api_client import get_api_endpoints, FallbackAPIClient, check_endpoint_health

# Test endpoint loading
active_endpoints = get_api_endpoints()
print(f'📊 Loaded {len(active_endpoints)} active endpoints')

for endpoint in active_endpoints:
    health = '🟢 UP' if check_endpoint_health(endpoint) else '🔴 DOWN'
    print(f'   {endpoint.name}: {health}')

# Test fallback client
client = FallbackAPIClient()
client.refresh_endpoints()

if client.endpoints:
    print(f'✅ Fallback client loaded {len(client.endpoints)} endpoints')
    current = client.get_current_endpoint()
    if current:
        print(f'🎯 Current endpoint: {current.name}')
else:
    print('❌ No endpoints available for fallback')
"

# Show final status
echo "📊 Final System Status"
python manage.py shell -c "
from streamapp.models import APIEndpoint
from streamapp.api_client import check_endpoint_health, FallbackAPIClient
from django.core.cache import cache

# Show active endpoints
active_endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
print(f'Active Endpoints: {active_endpoints.count()}')

for endpoint in active_endpoints:
    health = '🟢 UP' if check_endpoint_health(endpoint) else '🔴 DOWN'
    print(f'   {endpoint.name}: {health}')

# Show cache status
cache_status = '✅ CLEAN' if cache.get('api_endpoints') is None else '❌ STALE'
print(f'Cache Status: {cache_status}')

# Show fallback chain
client = FallbackAPIClient()
client.refresh_endpoints()
print(f'Fallback Chain: {len(client.endpoints)} endpoints loaded')
"

echo "🎉 Fallback system fix completed!" 