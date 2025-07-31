import os
import sys
import django
import time
import random
import requests
from unittest.mock import patch, MagicMock

# Tambahkan path proyek ke sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from streamapp.models import APIEndpoint
from streamapp.api_client import FallbackAPIClient

def setup_test_endpoints():
    """
    Membuat endpoint pengujian dengan domain sumber yang berbeda.
    """
    # Hapus semua endpoint yang ada
    APIEndpoint.objects.all().delete()
    
    # Buat endpoint pengujian
    endpoint1 = APIEndpoint.objects.create(
        name="API Test 1",
        url="http://localhost:8001/api/v1",
        source_domain="domain1.example.com",
        priority=100,
        is_active=True
    )
    
    endpoint2 = APIEndpoint.objects.create(
        name="API Test 2",
        url="http://localhost:8002/api/v1",
        source_domain="domain2.example.com",
        priority=50,
        is_active=True
    )
    
    endpoint3 = APIEndpoint.objects.create(
        name="API Test 3",
        url="http://localhost:8003/api/v1",
        source_domain="domain3.example.com",
        priority=10,
        is_active=True
    )
    
    return [endpoint1, endpoint2, endpoint3]

def mock_request_success(url, *args, **kwargs):
    """
    Mock untuk request yang berhasil.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success", "data": {"message": "OK"}}
    return mock_response

def mock_request_failure(url, *args, **kwargs):
    """
    Mock untuk request yang gagal.
    """
    raise requests.exceptions.RequestException("Connection error")

def test_domain_autoswitch():
    """
    Menguji auto-switch domain sumber saat API endpoint berubah.
    """
    # Setup endpoint pengujian
    endpoints = setup_test_endpoints()
    
    # Buat instance FallbackAPIClient
    client = FallbackAPIClient()
    
    # Test 1: Semua endpoint aktif, gunakan endpoint dengan prioritas tertinggi
    with patch.object(requests.Session, 'get', side_effect=mock_request_success):
        result = client.get("test-endpoint")
        current_api = client.current_api
        current_domain = client.get_current_source_domain()
        
        print(f"Test 1: Semua endpoint aktif")
        print(f"  Current API: {current_api}")
        print(f"  Current Domain: {current_domain}")
        print(f"  Expected Domain: {endpoints[0].source_domain}")
        assert current_domain == endpoints[0].source_domain, "Domain sumber tidak sesuai dengan endpoint prioritas tertinggi"
    
    # Test 2: Endpoint prioritas tertinggi gagal, gunakan endpoint prioritas kedua
    def mixed_response(url, *args, **kwargs):
        if "localhost:8001" in url:
            raise requests.exceptions.RequestException("Connection error")
        return mock_request_success(url, *args, **kwargs)
    
    with patch.object(requests.Session, 'get', side_effect=mixed_response):
        result = client.get("test-endpoint")
        current_api = client.current_api
        current_domain = client.get_current_source_domain()
        
        print(f"\nTest 2: Endpoint prioritas tertinggi gagal")
        print(f"  Current API: {current_api}")
        print(f"  Current Domain: {current_domain}")
        print(f"  Expected Domain: {endpoints[1].source_domain}")
        assert current_domain == endpoints[1].source_domain, "Domain sumber tidak beralih ke endpoint prioritas kedua"
    
    # Test 3: Endpoint prioritas kedua gagal, gunakan endpoint prioritas ketiga
    def mixed_response2(url, *args, **kwargs):
        if "localhost:8001" in url or "localhost:8002" in url:
            raise requests.exceptions.RequestException("Connection error")
        return mock_request_success(url, *args, **kwargs)
    
    with patch.object(requests.Session, 'get', side_effect=mixed_response2):
        result = client.get("test-endpoint")
        current_api = client.current_api
        current_domain = client.get_current_source_domain()
        
        print(f"\nTest 3: Endpoint prioritas kedua gagal")
        print(f"  Current API: {current_api}")
        print(f"  Current Domain: {current_domain}")
        print(f"  Expected Domain: {endpoints[2].source_domain}")
        assert current_domain == endpoints[2].source_domain, "Domain sumber tidak beralih ke endpoint prioritas ketiga"
    
    # Test 4: Endpoint prioritas tertinggi kembali aktif, gunakan endpoint prioritas tertinggi
    with patch.object(requests.Session, 'get', side_effect=mock_request_success):
        # Reset failed_endpoints untuk memastikan semua endpoint dicoba
        client.failed_endpoints = {}
        
        result = client.get("test-endpoint")
        current_api = client.current_api
        current_domain = client.get_current_source_domain()
        
        print(f"\nTest 4: Endpoint prioritas tertinggi kembali aktif")
        print(f"  Current API: {current_api}")
        print(f"  Current Domain: {current_domain}")
        print(f"  Expected Domain: {endpoints[0].source_domain}")
        assert current_domain == endpoints[0].source_domain, "Domain sumber tidak kembali ke endpoint prioritas tertinggi"
    
    print("\nSemua pengujian berhasil!")

if __name__ == "__main__":
    test_domain_autoswitch()