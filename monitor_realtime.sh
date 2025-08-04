#!/bin/bash

# Script untuk monitoring realtime sistem fallback API

echo "🚀 Starting Realtime Fallback System Monitor..."

# Aktifkan virtual environment
source venv/bin/activate

# Function untuk menampilkan status
show_status() {
    echo "📊 Current Status - $(date '+%H:%M:%S')"
    echo "=" * 50
    
    python manage.py shell -c "
from streamapp.models import APIEndpoint
from streamapp.api_client import check_endpoint_health, FallbackAPIClient, get_api_endpoints
from django.core.cache import cache

# Show active endpoints
active_endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
print(f'Active Endpoints: {active_endpoints.count()}')

for endpoint in active_endpoints:
    health = '🟢 UP' if check_endpoint_health(endpoint) else '🔴 DOWN'
    print(f'   {endpoint.name}: {health}')

# Show current fallback chain
client = FallbackAPIClient()
client.refresh_endpoints()
current = client.get_current_endpoint()

if current:
    print(f'🎯 Current endpoint: {current.name}')
    health = '🟢 UP' if check_endpoint_health(current) else '🔴 DOWN'
    print(f'   Health: {health}')
else:
    print('❌ No active endpoint')

# Show cache status
cache_status = '✅ CLEAN' if cache.get('api_endpoints') is None else '❌ STALE'
print(f'Cache: {cache_status}')
"
}

# Function untuk test fallback
test_fallback() {
    echo "🧪 Testing fallback..."
    python manage.py shell -c "
from streamapp.api_client import FallbackAPIClient

client = FallbackAPIClient()
client.refresh_endpoints()

if client.endpoints:
    print(f'✅ Loaded {len(client.endpoints)} endpoints')
    
    # Test fallback
    old_index = client.current_endpoint_index
    success = client._fallback_to_next_endpoint()
    
    if success:
        new_endpoint = client.get_current_endpoint()
        print(f'✅ Fallback successful: {new_endpoint.name}')
    else:
        print('❌ Fallback failed - no more endpoints')
else:
    print('❌ No endpoints available')
"
}

# Function untuk monitor realtime
monitor_realtime() {
    local duration=${1:-5}  # Default 5 minutes
    local interval=${2:-10}  # Default 10 seconds
    
    echo "⏱️  Starting realtime monitoring for $duration minutes (check every $interval seconds)..."
    echo "Press Ctrl+C to stop"
    echo ""
    
    local start_time=$(date +%s)
    local end_time=$((start_time + duration * 60))
    
    while [ $(date +%s) -lt $end_time ]; do
        show_status
        echo ""
        sleep $interval
    done
    
    echo "✅ Realtime monitoring completed"
}

# Main menu
echo "📋 Fallback System Monitor"
echo "1. Show current status"
echo "2. Test fallback system"
echo "3. Start realtime monitoring"
echo "4. Exit"
echo ""

read -p "Choose option (1-4): " choice

case $choice in
    1)
        show_status
        ;;
    2)
        test_fallback
        ;;
    3)
        read -p "Enter monitoring duration in minutes (default 5): " duration
        duration=${duration:-5}
        read -p "Enter check interval in seconds (default 10): " interval
        interval=${interval:-10}
        monitor_realtime $duration $interval
        ;;
    4)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac 