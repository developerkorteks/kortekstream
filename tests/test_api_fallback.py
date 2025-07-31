import os
import sys
import time
import threading
import subprocess
import requests
import json
import django
from django.core.management import call_command

# Tambahkan path proyek ke sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

# Import model dan client setelah setup Django
from streamapp.models import APIEndpoint, APIMonitor
from streamapp.api_client import api_client

# Konfigurasi server dummy
DUMMY_SERVERS = [
    {"port": 8001, "name": "API Server 1", "priority": 100},
    {"port": 8002, "name": "API Server 2", "priority": 50},
    {"port": 8003, "name": "API Server 3", "priority": 10},
]

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
    servers = []
    for server_config in DUMMY_SERVERS:
        server = DummyAPIServer(server_config["port"], server_config["name"])
        server.start()
        servers.append(server)
        
        # Buat endpoint di database
        APIEndpoint.objects.create(
            name=server_config["name"],
            url=f"http://localhost:{server_config['port']}",
            priority=server_config["priority"],
            is_active=True
        )
    
    # Tunggu semua server siap
    time.sleep(2)
    
    return servers

def cleanup_dummy_servers(servers):
    """
    Membersihkan server API dummy.
    """
    for server in servers:
        server.stop()
    
    # Hapus semua endpoint
    APIEndpoint.objects.all().delete()

def test_api_fallback():
    """
    Menguji implementasi fallback API.
    """
    print("\n=== Menguji Implementasi Fallback API ===\n")
    
    # Setup server dummy
    servers = setup_dummy_servers()
    
    try:
        # Refresh endpoint di API client
        api_client.refresh_endpoints()
        
        print("\n1. Menguji semua server aktif...")
        try:
            # Coba akses endpoint home
            result = api_client.get("home")
            print(f"Berhasil mengakses endpoint home: {result}")
        except Exception as e:
            print(f"Error saat mengakses endpoint home: {e}")
        
        print("\n2. Menguji server prioritas tertinggi down...")
        # Matikan server prioritas tertinggi
        servers[0].stop()
        time.sleep(1)
        
        try:
            # Coba akses endpoint home lagi
            result = api_client.get("home")
            print(f"Berhasil mengakses endpoint home melalui fallback: {result}")
        except Exception as e:
            print(f"Error saat mengakses endpoint home: {e}")
        
        print("\n3. Menguji server prioritas kedua down...")
        # Matikan server prioritas kedua
        servers[1].stop()
        time.sleep(1)
        
        try:
            # Coba akses endpoint home lagi
            result = api_client.get("home")
            print(f"Berhasil mengakses endpoint home melalui fallback kedua: {result}")
        except Exception as e:
            print(f"Error saat mengakses endpoint home: {e}")
        
        print("\n4. Menguji semua server down...")
        # Matikan semua server
        servers[2].stop()
        time.sleep(1)
        
        try:
            # Coba akses endpoint home lagi
            result = api_client.get("home")
            print(f"Berhasil mengakses endpoint home: {result}")
        except Exception as e:
            print(f"Error saat mengakses endpoint home (diharapkan): {e}")
        
        print("\n5. Menguji pemulihan server...")
        # Hidupkan kembali server prioritas tertinggi
        servers[0].start()
        time.sleep(2)
        
        # Refresh endpoint di API client
        api_client.refresh_endpoints()
        
        try:
            # Coba akses endpoint home lagi
            result = api_client.get("home")
            print(f"Berhasil mengakses endpoint home setelah pemulihan: {result}")
        except Exception as e:
            print(f"Error saat mengakses endpoint home setelah pemulihan: {e}")
        
        print("\n6. Menjalankan pemeriksaan status API...")
        # Jalankan pemeriksaan status API
        call_command('check_api_status', verbosity=2)
        
        # Tampilkan hasil pemeriksaan
        monitors = APIMonitor.objects.all()
        print(f"\nHasil pemeriksaan status API ({monitors.count()} monitor):")
        for monitor in monitors:
            print(f"- {monitor.endpoint.name} - {monitor.endpoint_path}: {monitor.status}")
        
        print("\n=== Pengujian Selesai ===\n")
        
    finally:
        # Cleanup
        cleanup_dummy_servers(servers)

if __name__ == "__main__":
    test_api_fallback()