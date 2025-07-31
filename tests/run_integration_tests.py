#!/usr/bin/env python3
"""
Skrip untuk menjalankan semua tes integrasi
"""
import os
import sys
import logging
import time
import subprocess
import argparse

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integration_tests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_test(test_script, description):
    """
    Menjalankan skrip tes dan mencatat hasilnya
    """
    logger.info(f"=== Menjalankan {description} ===")
    start_time = time.time()
    
    try:
        # Jalankan skrip tes
        result = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True,
            check=False
        )
        
        elapsed = time.time() - start_time
        
        # Catat output
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(line)
        
        # Catat error
        if result.stderr:
            for line in result.stderr.splitlines():
                logger.error(line)
        
        # Catat hasil
        if result.returncode == 0:
            logger.info(f"✅ {description} berhasil dalam {elapsed:.2f} detik")
            return True
        else:
            logger.error(f"❌ {description} gagal dengan kode: {result.returncode}")
            return False
    except Exception as e:
        logger.error(f"❌ {description} gagal dengan error: {e}")
        return False

def main():
    """
    Fungsi utama
    """
    parser = argparse.ArgumentParser(description='Menjalankan tes integrasi')
    parser.add_argument('--api-only', action='store_true', help='Hanya jalankan tes API')
    parser.add_argument('--views-only', action='store_true', help='Hanya jalankan tes views')
    args = parser.parse_args()
    
    # Dapatkan path skrip tes
    current_dir = os.path.dirname(os.path.abspath(__file__))
    api_test_script = os.path.join(current_dir, 'test_api_connection.py')
    views_test_script = os.path.join(current_dir, 'test_django_views.py')
    
    # Jalankan tes
    results = {}
    
    if not args.views_only:
        results['api'] = run_test(api_test_script, "Tes koneksi API")
    
    if not args.api_only:
        results['views'] = run_test(views_test_script, "Tes Django views")
    
    # Tampilkan ringkasan
    logger.info("=== Ringkasan Hasil Tes ===")
    for test_name, success in results.items():
        status = "✅ BERHASIL" if success else "❌ GAGAL"
        logger.info(f"{test_name}: {status}")
    
    # Tentukan status keluar
    if all(results.values()):
        logger.info("🎉 Semua tes berhasil!")
        return 0
    else:
        logger.error("❌ Beberapa tes gagal!")
        return 1

if __name__ == "__main__":
    sys.exit(main())