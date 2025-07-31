import sys
import os
import logging
import django
import unittest
import asyncio
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tambahkan path proyek ke sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Konfigurasi Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kortekstream.settings')
django.setup()

# Import views
try:
    from streamapp.views import (
        index,
        detail_anime,
        all_list_anime_terbaru,
        all_list_jadwal_rilis,
        all_list_movie,
        detail_episode_video,
        search,
        user_collection,
    )
    logger.info("Berhasil mengimpor views")
except ImportError as e:
    logger.error(f"Gagal mengimpor views: {e}")
    sys.exit(1)

class TestDjangoViews(TestCase):
    """
    Tes untuk Django views
    """
    def setUp(self):
        self.factory = RequestFactory()
    
    async def test_index_view(self):
        """
        Tes untuk view index
        """
        logger.info("=== Menguji view index ===")
        request = self.factory.get('/')
        
        try:
            response = await index(request)
            
            if response.status_code == 200:
                logger.info("✅ View index berhasil")
            else:
                logger.error(f"❌ View index gagal dengan status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ View index gagal dengan error: {e}")
    
    async def test_detail_anime_view(self):
        """
        Tes untuk view detail_anime
        """
        logger.info("=== Menguji view detail_anime ===")
        # Gunakan slug anime yang valid
        anime_slug = "naruto"
        request = self.factory.get(f'/anime/{anime_slug}/')
        
        try:
            response = await detail_anime(request, anime_slug=anime_slug)
            
            if response.status_code == 200:
                logger.info("✅ View detail_anime berhasil")
            else:
                logger.error(f"❌ View detail_anime gagal dengan status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ View detail_anime gagal dengan error: {e}")
    
    async def test_all_list_anime_terbaru_view(self):
        """
        Tes untuk view all_list_anime_terbaru
        """
        logger.info("=== Menguji view all_list_anime_terbaru ===")
        request = self.factory.get('/anime-terbaru/')
        
        try:
            response = await all_list_anime_terbaru(request)
            
            if response.status_code == 200:
                logger.info("✅ View all_list_anime_terbaru berhasil")
            else:
                logger.error(f"❌ View all_list_anime_terbaru gagal dengan status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ View all_list_anime_terbaru gagal dengan error: {e}")
    
    async def test_all_list_jadwal_rilis_view(self):
        """
        Tes untuk view all_list_jadwal_rilis
        """
        logger.info("=== Menguji view all_list_jadwal_rilis ===")
        request = self.factory.get('/jadwal-rilis/')
        
        try:
            response = await all_list_jadwal_rilis(request)
            
            if response.status_code == 200:
                logger.info("✅ View all_list_jadwal_rilis berhasil")
            else:
                logger.error(f"❌ View all_list_jadwal_rilis gagal dengan status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ View all_list_jadwal_rilis gagal dengan error: {e}")
    
    async def test_all_list_movie_view(self):
        """
        Tes untuk view all_list_movie
        """
        logger.info("=== Menguji view all_list_movie ===")
        request = self.factory.get('/movie/')
        
        try:
            response = await all_list_movie(request)
            
            if response.status_code == 200:
                logger.info("✅ View all_list_movie berhasil")
            else:
                logger.error(f"❌ View all_list_movie gagal dengan status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ View all_list_movie gagal dengan error: {e}")
    
    async def test_search_view(self):
        """
        Tes untuk view search
        """
        logger.info("=== Menguji view search ===")
        query = "naruto"
        request = self.factory.get(f'/search/?q={query}')
        
        try:
            response = await search(request)
            
            if response.status_code == 200:
                logger.info("✅ View search berhasil")
            else:
                logger.error(f"❌ View search gagal dengan status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ View search gagal dengan error: {e}")

# Fungsi untuk menjalankan tes async
def run_async_test(test_func):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_func())

if __name__ == "__main__":
    # Jalankan tes
    test_views = TestDjangoViews()
    test_views.setUp()
    
    # Jalankan tes secara async
    run_async_test(test_views.test_index_view)
    run_async_test(test_views.test_detail_anime_view)
    run_async_test(test_views.test_all_list_anime_terbaru_view)
    run_async_test(test_views.test_all_list_jadwal_rilis_view)
    run_async_test(test_views.test_all_list_movie_view)
    run_async_test(test_views.test_search_view)