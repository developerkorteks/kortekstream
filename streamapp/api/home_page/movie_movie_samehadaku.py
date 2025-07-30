import requests
from bs4 import BeautifulSoup
import re
import sys
import os
import concurrent.futures
import functools
from django.core.cache import cache

# Baris ini diasumsikan benar untuk struktur proyek Anda
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from anime_detail import detail_anime

# Decorator untuk caching (Tetap dipertahankan)
def cache_result(ttl=60*60*24):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"cover_cache_{func.__name__}_{args[0]}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            result = func(*args, **kwargs)
            if result:
                cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

def extract_anime_slug_from_url(url):
    """Mengekstrak slug anime dari URL untuk membangun URL detail."""
    match = re.search(r'/anime/([^/]+)/', url)
    if match:
        return match.group(1)
    return None

@cache_result()
def get_better_cover(anime_slug):
    """Mendapatkan URL cover dengan kualitas lebih baik dari halaman detail anime."""
    if not anime_slug:
        return None
    try:
        url = f"https://v1.samehadaku.how/anime/{anime_slug}/"
        anime_details = detail_anime.scrape_anime_details(url)
        if anime_details and anime_details.get('thumbnail_url') and anime_details['thumbnail_url'] != "N/A":
            return anime_details['thumbnail_url']
    except Exception as e:
        print(f"Error saat mengambil cover untuk {anime_slug}: {e}")
    return None

def scrape_project_movies_with_soup(soup, get_better_covers=True):
    """
    Mengambil data movie dari objek BeautifulSoup dengan selector yang sudah diperbaiki.
    """
    project_movies = []
    
    # --- PERUBAHAN UTAMA: Selector Langsung ke Target ---
    # Langsung menargetkan setiap item 'li' di dalam widget series di sidebar
    # Ini jauh lebih stabil daripada mencari berdasarkan teks 'h3'
    movie_items = soup.select("aside#sidebar .widgetseries ul li")
    
    for item in movie_items:
        title_el = item.select_one("h2 a.series")
        if not title_el:
            continue

        # Mengambil genre
        genre_elements = item.select(".lftinfo span a")
        genres = [genre.text.strip() for genre in genre_elements]

        # Mengambil tanggal rilis
        release_date_el = item.select_one(".lftinfo span:last-of-type")
        release_date = release_date_el.text.strip() if release_date_el and not release_date_el.find('a') else "-"

        project_movies.append({
            "judul": title_el.text.strip(),
            "url": title_el.get("href"),
            "cover": item.select_one("img").get("src") if item.select_one("img") else "-",
            "genres": genres,
            "tanggal": release_date
        })

    if get_better_covers and project_movies:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_movie_index = {
                executor.submit(get_better_cover, extract_anime_slug_from_url(movie['url'])): i
                for i, movie in enumerate(project_movies)
            }
            for future in concurrent.futures.as_completed(future_to_movie_index):
                index = future_to_movie_index[future]
                try:
                    better_cover = future.result()
                    if better_cover:
                        project_movies[index]['cover'] = better_cover
                except Exception as exc:
                    print(f"Gagal memproses cover untuk movie di index {index}: {exc}")

    return project_movies

def scrape_project_movies(get_better_covers=True):
    """
    Fungsi utama yang akan dipanggil oleh handler API Anda.
    """
    url = "https://v1.samehadaku.how/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")
        return scrape_project_movies_with_soup(soup, get_better_covers)
    except requests.RequestException as e:
        print(f"Error saat mengambil halaman utama: {e}")
        return []

# Bagian ini untuk pengujian, pastikan Django terkonfigurasi saat menjalankannya
if __name__ == '__main__':
    print("Skrip ini ditujukan untuk diimpor dan dijalankan dalam proyek Django.")
    print("Mengkonfigurasi pengaturan Django sementara untuk pengujian...")
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            CACHES = {
                'default': {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                }
            }
        )
    # import json
    # movies = scrape_project_movies(get_better_covers=False)
    # print(json.dumps(movies, indent=4, ensure_ascii=False))