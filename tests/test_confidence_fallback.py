import sys
import requests
import json
import time
import subprocess
import os
import django
from django.core.management import call_command

# Tambahkan path proyek ke sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

# Import model dan client setelah setup Django
from streamapp.models import APIEndpoint, APIMonitor
from streamapp.api_client import api_client, get_movie_list

# Path ke file FastAPI dummy
FASTAPI_DUMMY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dummy_fastapi_server.py')

class DummyAPIServer:
    """
    Kelas untuk mengelola server API dummy.
    """
    def __init__(self, port, name):
        self.port = port
        self.name = name
        self.process = None
        self.url = f"http://localhost:{port}"
    
    def start(self):
        """
        Memulai server API dummy.
        """
        print(f"Memulai server {self.name} di port {self.port}...")
        self.process = subprocess.Popen(
            [sys.executable, FASTAPI_DUMMY_PATH, str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Tunggu server siap
        time.sleep(2)
        print(f"Server {self.name} berjalan di {self.url}")
    
    def stop(self):
        """
        Menghentikan server API dummy.
        """
        if self.process:
            print(f"Menghentikan server {self.name}...")
            self.process.terminate()
            self.process.wait()
            self.process = None
            print(f"Server {self.name} dihentikan")
    
    def is_running(self):
        """
        Memeriksa apakah server API dummy berjalan.
        """
        if not self.process:
            return False
        
        try:
            response = requests.get(f"{self.url}/health", timeout=1)
            return response.status_code == 200
        except:
            return False

def setup_dummy_servers():
    """
    Menyiapkan server API dummy dan endpoint di database.
    """
    # Hapus semua endpoint yang ada
    APIEndpoint.objects.all().delete()
    
    # Buat server dummy
    primary_server = DummyAPIServer(8001, "Primary API Server")
    fallback_server = DummyAPIServer(8002, "Fallback API Server")
    
    # Mulai server
    primary_server.start()
    fallback_server.start()
    
    # Buat endpoint di database
    APIEndpoint.objects.create(
        name="Primary API",
        url="http://localhost:8001",
        priority=100,
        is_active=True
    )
    
    APIEndpoint.objects.create(
        name="Fallback API",
        url="http://localhost:8002",
        priority=50,
        is_active=True
    )
    
    # Tunggu semua server siap
    time.sleep(2)
    
    return [primary_server, fallback_server]

def cleanup_dummy_servers(servers):
    """
    Membersihkan server API dummy.
    """
    for server in servers:
        server.stop()
    
    # Hapus semua endpoint
    APIEndpoint.objects.all().delete()

def test_confidence_fallback():
    """
    Menguji apakah mekanisme fallback berfungsi dengan benar ketika confidence score < 0.5.
    """
    print("\n=== Menguji Mekanisme Fallback dengan Confidence Score ===\n")
    
    # Setup server dummy
    servers = setup_dummy_servers()
    
    try:
        # Refresh endpoint di API client
        api_client.refresh_endpoints()
        
        print("\n1. Menguji confidence score tinggi (0.8) pada server utama...")
        try:
            # Coba akses endpoint movie dengan confidence score tinggi
            response = requests.get("http://localhost:8001/api/v1/movie/?confidence=0.8")
            result = response.json()
            print(f"Respons dari server utama: {result.get('confidence_score')}")
            
            # Gunakan API client untuk mengakses endpoint movie
            movie_data = get_movie_list(1)
            
            # Dapatkan informasi server yang digunakan
            endpoint = api_client.current_api.get('endpoint')
            server_name = endpoint.name if endpoint and hasattr(endpoint, 'name') else 'Unknown'
            print(f"API client menggunakan server: {server_name}")
            
            print(f"Jumlah movie yang diterima: {len(movie_data) if isinstance(movie_data, list) else 'N/A'}")
        except Exception as e:
            print(f"Error saat mengakses endpoint movie dengan confidence score tinggi: {e}")
        
        print("\n2. Menguji confidence score rendah (0.3) pada server utama...")
        try:
            # Coba akses endpoint movie dengan confidence score rendah
            response = requests.get("http://localhost:8001/api/v1/movie/?confidence=0.3")
            result = response.json()
            print(f"Respons dari server utama: {result.get('confidence_score')}")
            
            # Gunakan API client untuk mengakses endpoint movie
            movie_data = get_movie_list(1)
            
            # Dapatkan informasi server yang digunakan
            endpoint = api_client.current_api.get('endpoint')
            server_name = endpoint.name if endpoint and hasattr(endpoint, 'name') else 'Unknown'
            print(f"API client menggunakan server: {server_name}")
            
            print(f"Jumlah movie yang diterima: {len(movie_data) if isinstance(movie_data, list) else 'N/A'}")
            
            # Periksa apakah API client menggunakan server fallback
            if endpoint and hasattr(endpoint, 'name') and endpoint.name == "Fallback API":
                print("Berhasil! API client menggunakan server fallback ketika confidence score < 0.5")
            else:
                print("Gagal! API client tidak menggunakan server fallback meskipun confidence score < 0.5")
        except Exception as e:
            print(f"Error saat mengakses endpoint movie dengan confidence score rendah: {e}")
        
        print("\n=== Pengujian Selesai ===\n")
        
    finally:
        # Cleanup
        cleanup_dummy_servers(servers)

if __name__ == "__main__":
    test_confidence_fallback()