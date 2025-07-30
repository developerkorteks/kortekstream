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

# Decorator untuk caching (Tetap dipertahankan sesuai permintaan)
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
        # Log error ini dengan sistem logging Django Anda jika perlu
        print(f"Error saat mengambil cover untuk {anime_slug}: {e}")
    return None

def scrape_anime_terbaru_with_soup(soup, get_better_covers=True):
    """
    Mengambil data dari objek BeautifulSoup dengan selector yang sudah diperbaiki.
    """
    anime_terbaru_list = []
    # Selector yang lebih spesifik untuk menargetkan daftar anime terbaru
    items = soup.select(".post-show > ul > li")

    for li in items:
        title_el = li.select_one("h2.entry-title a")
        if not title_el:
            continue

        # --- PERBAIKAN LOGIKA PENGAMBILAN DATA ---
        
        # Mengambil episode dengan selector yang lebih stabil dan membersihkan teksnya
        episode_el = li.select_one(".dtla span:nth-of-type(1)")
        episode = episode_el.get_text(strip=True).replace("Episode", "").strip() if episode_el else "-"

        # Mengambil posted_by dengan selector yang benar
        posted_by_el = li.select_one(".author.vcard author")
        posted_by = posted_by_el.text.strip() if posted_by_el else "-"

        # Mengambil tanggal rilis dan membersihkan teksnya
        released_on_el = li.select_one(".dtla span:nth-of-type(3)")
        rilis = released_on_el.get_text(strip=True).replace("Released on:", "").strip() if released_on_el else "-"
        
        # -------------------------------------------

        url = title_el["href"]
        cover = li.select_one("img")["src"] if li.select_one("img") else "-"

        anime = {
            "judul": title_el.text.strip(),
            "url": url,
            "cover": cover,
            "episode": episode,
            "posted_by": posted_by,
            "rilis": rilis
        }
        anime_terbaru_list.append(anime)

    if get_better_covers:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_anime_index = {
                executor.submit(get_better_cover, extract_anime_slug_from_url(anime['url'])): i
                for i, anime in enumerate(anime_terbaru_list)
            }
            for future in concurrent.futures.as_completed(future_to_anime_index):
                index = future_to_anime_index[future]
                try:
                    better_cover = future.result()
                    if better_cover:
                        anime_terbaru_list[index]['cover'] = better_cover
                except Exception as exc:
                    print(f"Gagal memproses cover untuk anime di index {index}: {exc}")

    return anime_terbaru_list

def scrape_anime_terbaru(get_better_covers=True):
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
        return scrape_anime_terbaru_with_soup(soup, get_better_covers)
    except requests.RequestException as e:
        print(f"Error saat mengambil halaman utama: {e}")
        return []

# Baris ini hanya untuk pengujian, jangan jalankan file ini secara langsung di produksi
if __name__ == '__main__':
    # Untuk menjalankan file ini secara langsung, Anda perlu setup minimal Django
    print("Skrip ini ditujukan untuk diimpor dan dijalankan dalam proyek Django.")
    print("Mengkonfigurasi pengaturan Django sementara untuk pengujian...")
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            CACHES = {
                'default': {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                    'LOCATION': 'unique-snowflake',
                }
            }
        )
    # Menjalankan fungsi utama untuk demonstrasi
    # import json
    # latest_anime = scrape_anime_terbaru(get_better_covers=False) # Dimatikan agar tidak memanggil detail_anime
    # print(json.dumps(latest_anime, indent=4, ensure_ascii=False))