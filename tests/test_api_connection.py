import sys
import os
import requests
import logging
import time
import json

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tambahkan path proyek ke sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Definisikan API_BASE_URL secara langsung
API_BASE_URL = "http://localhost:8001/api/v1"

# Fungsi-fungsi API client sederhana
def get_home_data():
    """Get home page data."""
    try:
        response = requests.get(f"{API_BASE_URL}/home")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting home data: {e}")
        return {}

def get_anime_detail(anime_slug):
    """Get anime details."""
    try:
        response = requests.get(f"{API_BASE_URL}/anime-detail", params={"anime_slug": anime_slug})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting anime detail: {e}")
        return {}

def get_episode_detail(episode_url):
    """Get episode details."""
    try:
        response = requests.get(f"{API_BASE_URL}/episode-detail", params={"episode_url": episode_url})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting episode detail: {e}")
        return {}

def get_jadwal_rilis(day=None):
    """Get release schedule."""
    try:
        endpoint = "jadwal-rilis"
        if day:
            endpoint = f"{endpoint}/{day.lower()}"
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting jadwal rilis: {e}")
        return {} if day is None else []

def get_anime_terbaru(page=1):
    """Get latest anime."""
    try:
        response = requests.get(f"{API_BASE_URL}/anime-terbaru", params={"page": page})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting anime terbaru: {e}")
        return []

def get_movie_list(page=1):
    """Get movie list."""
    try:
        response = requests.get(f"{API_BASE_URL}/movie", params={"page": page})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting movie list: {e}")
        return []

def search_anime(query):
    """Search for anime."""
    try:
        response = requests.get(f"{API_BASE_URL}/search", params={"query": query})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error searching anime: {e}")
        return []

def test_api_connection():
    """
    Tes koneksi ke API FastAPI
    """
    logger.info("=== Mulai pengujian koneksi API ===")
    
    # Tes get_home_data
    try:
        logger.info("Menguji get_home_data...")
        start_time = time.time()
        home_data = get_home_data()
        elapsed = time.time() - start_time
        
        if home_data:
            logger.info(f"✅ get_home_data berhasil dalam {elapsed:.2f} detik")
            logger.info(f"  - Jumlah anime terbaru: {len(home_data.get('new_eps', []))}")
            logger.info(f"  - Jumlah movie: {len(home_data.get('movies', []))}")
            logger.info(f"  - Jumlah anime mingguan: {len(home_data.get('top10', []))}")
            logger.info(f"  - Jumlah hari jadwal: {len(home_data.get('jadwal_rilis', {}))}")
        else:
            logger.error("❌ get_home_data mengembalikan data kosong")
    except Exception as e:
        logger.error(f"❌ get_home_data gagal: {e}")
    
    # Tes get_anime_terbaru
    try:
        logger.info("Menguji get_anime_terbaru...")
        start_time = time.time()
        anime_terbaru = get_anime_terbaru(1)
        elapsed = time.time() - start_time
        
        if anime_terbaru:
            logger.info(f"✅ get_anime_terbaru berhasil dalam {elapsed:.2f} detik")
            logger.info(f"  - Jumlah anime: {len(anime_terbaru)}")
            
            # Ambil anime_slug dari anime pertama untuk pengujian get_anime_detail
            if anime_terbaru and len(anime_terbaru) > 0:
                anime_slug = None
                for anime in anime_terbaru:
                    if 'url' in anime and 'anime/' in anime['url']:
                        import re
                        match = re.search(r'anime/([^/]+)', anime['url'])
                        if match:
                            anime_slug = match.group(1)
                            break
                
                if anime_slug:
                    logger.info(f"  - Anime slug untuk pengujian: {anime_slug}")
                    
                    # Tes get_anime_detail
                    try:
                        logger.info(f"Menguji get_anime_detail dengan slug: {anime_slug}...")
                        start_time = time.time()
                        anime_detail = get_anime_detail(anime_slug)
                        elapsed = time.time() - start_time
                        
                        if anime_detail:
                            logger.info(f"✅ get_anime_detail berhasil dalam {elapsed:.2f} detik")
                            logger.info(f"  - Judul anime: {anime_detail.get('title', 'N/A')}")
                            logger.info(f"  - Jumlah episode: {len(anime_detail.get('episode_list', []))}")
                            
                            # Ambil episode_url dari episode pertama untuk pengujian get_episode_detail
                            if 'episode_list' in anime_detail and anime_detail['episode_list']:
                                episode_url = anime_detail['episode_list'][0].get('episode_url')
                                
                                if episode_url:
                                    logger.info(f"  - Episode URL untuk pengujian: {episode_url}")
                                    
                                    # Tes get_episode_detail
                                    try:
                                        logger.info(f"Menguji get_episode_detail...")
                                        start_time = time.time()
                                        episode_detail = get_episode_detail(episode_url)
                                        elapsed = time.time() - start_time
                                        
                                        if episode_detail:
                                            logger.info(f"✅ get_episode_detail berhasil dalam {elapsed:.2f} detik")
                                            logger.info(f"  - Judul episode: {episode_detail.get('title', 'N/A')}")
                                            logger.info(f"  - Jumlah video: {len(episode_detail.get('video_urls', []))}")
                                        else:
                                            logger.error("❌ get_episode_detail mengembalikan data kosong")
                                    except Exception as e:
                                        logger.error(f"❌ get_episode_detail gagal: {e}")
                        else:
                            logger.error("❌ get_anime_detail mengembalikan data kosong")
                    except Exception as e:
                        logger.error(f"❌ get_anime_detail gagal: {e}")
        else:
            logger.error("❌ get_anime_terbaru mengembalikan data kosong")
    except Exception as e:
        logger.error(f"❌ get_anime_terbaru gagal: {e}")
    
    # Tes get_jadwal_rilis
    try:
        logger.info("Menguji get_jadwal_rilis...")
        start_time = time.time()
        jadwal_rilis = get_jadwal_rilis()
        elapsed = time.time() - start_time
        
        if jadwal_rilis:
            logger.info(f"✅ get_jadwal_rilis berhasil dalam {elapsed:.2f} detik")
            
            # Periksa apakah jadwal_rilis adalah dictionary atau list
            if isinstance(jadwal_rilis, dict):
                logger.info(f"  - Jumlah hari: {len(jadwal_rilis)}")
                
                # Tes get_jadwal_rilis untuk hari tertentu
                if len(jadwal_rilis) > 0:
                    day = list(jadwal_rilis.keys())[0]
                    
                    try:
                        logger.info(f"Menguji get_jadwal_rilis untuk hari {day}...")
                        start_time = time.time()
                        jadwal_hari = get_jadwal_rilis(day)
                        elapsed = time.time() - start_time
                        
                        if jadwal_hari:
                            logger.info(f"✅ get_jadwal_rilis({day}) berhasil dalam {elapsed:.2f} detik")
                            logger.info(f"  - Jumlah anime: {len(jadwal_hari)}")
                        else:
                            logger.error(f"❌ get_jadwal_rilis({day}) mengembalikan data kosong")
                    except Exception as e:
                        logger.error(f"❌ get_jadwal_rilis({day}) gagal: {e}")
            else:
                # Jika jadwal_rilis adalah list, coba hari-hari umum
                logger.info(f"  - Jadwal rilis adalah list dengan {len(jadwal_rilis)} item")
                
                # Tes get_jadwal_rilis untuk hari tertentu
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    try:
                        logger.info(f"Menguji get_jadwal_rilis untuk hari {day}...")
                        start_time = time.time()
                        jadwal_hari = get_jadwal_rilis(day)
                        elapsed = time.time() - start_time
                        
                        if jadwal_hari:
                            logger.info(f"✅ get_jadwal_rilis({day}) berhasil dalam {elapsed:.2f} detik")
                            logger.info(f"  - Jumlah anime: {len(jadwal_hari)}")
                        else:
                            logger.warning(f"⚠️ get_jadwal_rilis({day}) mengembalikan data kosong")
                        
                        # Hanya tes satu hari untuk menghemat waktu
                        break
                    except Exception as e:
                        logger.error(f"❌ get_jadwal_rilis({day}) gagal: {e}")
                        break
        else:
            logger.error("❌ get_jadwal_rilis mengembalikan data kosong")
    except Exception as e:
        logger.error(f"❌ get_jadwal_rilis gagal: {e}")
    
    # Tes get_movie_list
    try:
        logger.info("Menguji get_movie_list...")
        start_time = time.time()
        movie_list = get_movie_list(1)
        elapsed = time.time() - start_time
        
        if movie_list:
            logger.info(f"✅ get_movie_list berhasil dalam {elapsed:.2f} detik")
            logger.info(f"  - Jumlah movie: {len(movie_list)}")
        else:
            logger.error("❌ get_movie_list mengembalikan data kosong")
    except Exception as e:
        logger.error(f"❌ get_movie_list gagal: {e}")
    
    # Tes search_anime
    try:
        query = "naruto"
        logger.info(f"Menguji search_anime dengan query: {query}...")
        start_time = time.time()
        search_results = search_anime(query)
        elapsed = time.time() - start_time
        
        if search_results:
            logger.info(f"✅ search_anime berhasil dalam {elapsed:.2f} detik")
            logger.info(f"  - Jumlah hasil: {len(search_results)}")
        else:
            logger.error("❌ search_anime mengembalikan data kosong")
    except Exception as e:
        logger.error(f"❌ search_anime gagal: {e}")
    
    logger.info("=== Pengujian koneksi API selesai ===")

if __name__ == "__main__":
    test_api_connection()