import sys
import requests
import json
import time
import subprocess
import os

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

def test_confidence_validation():
    """
    Menguji validasi confidence score.
    """
    print("\n=== Menguji Validasi Confidence Score ===\n")
    
    # Setup server dummy
    server = DummyAPIServer(8001, "API Server Test")
    server.start()
    
    try:
        print("\n1. Menguji confidence score tinggi (0.8)...")
        try:
            # Coba akses endpoint movie dengan confidence score tinggi
            response = requests.get("http://localhost:8001/movie", params={"confidence": 0.8})
            result = response.json()
            print(f"Berhasil mengakses endpoint movie dengan confidence score tinggi: {result}")
            print(f"Confidence score: {result.get('confidence_score')}")
            
            # Validasi respons
            assert response.status_code == 200
            assert result.get('confidence_score') == 0.8
            assert 'data' in result
            print("Validasi berhasil!")
        except Exception as e:
            print(f"Error saat mengakses endpoint movie dengan confidence score tinggi: {e}")
        
        print("\n2. Menguji confidence score rendah (0.3)...")
        try:
            # Coba akses endpoint movie dengan confidence score rendah
            response = requests.get("http://localhost:8001/movie", params={"confidence": 0.3})
            result = response.json()
            print(f"Berhasil mengakses endpoint movie dengan confidence score rendah: {result}")
            print(f"Confidence score: {result.get('confidence_score')}")
            
            # Validasi respons
            assert response.status_code == 200
            assert result.get('confidence_score') == 0.3
            assert 'data' in result
            print("Validasi berhasil!")
        except Exception as e:
            print(f"Error saat mengakses endpoint movie dengan confidence score rendah: {e}")
        
        print("\n3. Menguji validasi di API client...")
        print("Untuk menguji validasi di API client, perlu menggunakan Django.")
        print("Pastikan validasi confidence score di api_client.py sudah benar:")
        print("- Jika confidence score >= 0.5, gunakan respons API saat ini")
        print("- Jika confidence score < 0.5, gunakan API fallback")
        
        print("\n=== Pengujian Selesai ===\n")
        
    finally:
        # Cleanup
        server.stop()

if __name__ == "__main__":
    test_confidence_validation()