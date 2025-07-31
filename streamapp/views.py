from django.shortcuts import render
from django.http import HttpResponse
from django.core.cache import cache
import asyncio
import time
import functools
import concurrent.futures
from .models import Advertisement
from django.utils import timezone
from django.db import models
from asgiref.sync import sync_to_async
import logging

from .api_client import (
    get_jadwal_rilis,
    get_anime_terbaru,
    get_movie_list,
    get_anime_detail,
    get_episode_detail,
    search_anime,
    get_home_data,
)

logger = logging.getLogger(__name__)

# Fungsi-fungsi ini tidak diperlukan lagi karena kita menggunakan API client

# Decorator untuk caching
def async_cache(ttl=60*15, prefix='view_cache_'):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Membuat cache key berdasarkan nama fungsi dan argumen
            cache_key = f"{prefix}{func.__name__}"
            
            # Jika ada argumen, tambahkan ke cache key
            if args:
                cache_key += f"_{args[0]}"
            # Mencoba mendapatkan data dari cache
            cached_data = await cache.aget(cache_key)
            if cached_data:
                return cached_data
            # Jika tidak ada di cache, jalankan fungsi asli
            result = await func(*args, **kwargs)
            # Simpan hasil ke cache
            await cache.aset(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# Fungsi untuk mendapatkan data anime terbaru dengan caching
@async_cache(ttl=60*10, prefix='anime_terbaru_')
async def get_anime_terbaru_data(page=1):
    """
    Fungsi untuk mendapatkan data anime terbaru dengan caching.
    """
    return await asyncio.to_thread(get_anime_terbaru, page)

# Fungsi untuk mendapatkan data movie dengan caching
@async_cache(ttl=60*30, prefix='movie_')
async def get_movie_data(page=1):
    """
    Fungsi untuk mendapatkan data movie dengan caching.
    """
    return await asyncio.to_thread(get_movie_list, page)

# Fungsi untuk mendapatkan data anime mingguan dengan caching
@async_cache(ttl=60*60, prefix='anime_mingguan_')
async def get_anime_mingguan_data():
    """
    Fungsi untuk mendapatkan data anime mingguan dengan caching.
    """
    home_data = await asyncio.to_thread(get_home_data)
    return home_data.get("top10", [])

# Fungsi untuk mendapatkan detail anime dengan caching
@async_cache(ttl=60*60*24, prefix='anime_detail_')  # Cache selama 24 jam
async def get_anime_detail_data(anime_slug):
    """
    Fungsi untuk mendapatkan detail anime dengan caching.
    """
    # Buat cache key yang unik untuk setiap anime_slug
    cache_key = f"anime_detail_{anime_slug}"
    stale_cache_key = f"stale_anime_detail_{anime_slug}"
    
    # Cek cache terlebih dahulu
    cached_data = await cache.aget(cache_key)
    if cached_data:
        logger.info(f"Menggunakan data cache untuk anime: {anime_slug}")
        return cached_data
    
    # Jika tidak ada di cache, ambil data baru menggunakan API client
    logger.info(f"Mengambil detail anime: {anime_slug}")
    
    try:
        # Gunakan sync_to_async untuk menjalankan get_anime_detail dalam thread terpisah
        # Ini mencegah error "You cannot call this from an async context"
        get_anime_detail_async = sync_to_async(get_anime_detail)
        result = await get_anime_detail_async(anime_slug)
        
        if result:
            logger.info(f"Berhasil mendapatkan data anime: {anime_slug}")
            # Simpan hasil ke cache
            await cache.aset(cache_key, result, 60*60*24)  # Cache selama 24 jam
            # Simpan juga sebagai cache lama untuk fallback
            await cache.aset(stale_cache_key, result, 60*60*24*7)  # Cache selama 7 hari
            return result
        else:
            logger.warning(f"API mengembalikan data kosong untuk anime: {anime_slug}")
            # Cek apakah ada data cache lama yang bisa digunakan
            stale_cache = await cache.aget(stale_cache_key)
            if stale_cache:
                logger.info(f"Menggunakan data cache lama untuk anime: {anime_slug}")
                return stale_cache
            
            # Jika tidak ada cache lama, kembalikan objek dengan flag error
            logger.warning(f"Data anime tidak ditemukan untuk slug: {anime_slug}")
            return {
                "error": True,
                "message": f"Anime dengan slug '{anime_slug}' tidak ditemukan",
                "title": f"Anime {anime_slug}",
                "thumbnail_url": "/static/images/placeholder.jpg",
                "url_cover": "/static/images/placeholder.jpg",
                "sinopsis": "Data anime tidak ditemukan. Silakan coba lagi nanti atau kembali ke beranda.",
                "genres": [],
                "details": {"Status": "Unknown"},
                "episode_list": []
            }
    except Exception as e:
        logger.error(f"Error saat mengambil detail anime {anime_slug}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Coba gunakan cache lama jika ada error
        stale_cache = await cache.aget(stale_cache_key)
        if stale_cache:
            logger.info(f"Menggunakan data cache lama untuk anime: {anime_slug}")
            return stale_cache
        
        # Jika tidak ada cache lama, kembalikan objek dengan flag error
        return {
            "error": True,
            "message": f"Terjadi kesalahan saat memuat data anime: {str(e)}",
            "title": f"Anime {anime_slug}",
            "thumbnail_url": "/static/images/placeholder.jpg",
            "url_cover": "/static/images/placeholder.jpg",
            "sinopsis": "Terjadi kesalahan saat memuat data. Silakan coba lagi nanti atau kembali ke beranda.",
            "genres": [],
            "details": {"Status": "Unknown"},
            "episode_list": []
        }

# Create your views here.
async def index(request):
    """
    View untuk halaman utama.
    """
    # Cek cache untuk seluruh halaman dengan versioning
    cache_version = int(time.time() / (60 * 15))  # Versi berubah setiap 15 menit
    cached_data = await cache.aget(f'home_page_data_v{cache_version}')
    
    # Jika tidak ada di cache versi terbaru, coba cek cache standar
    if not cached_data:
        cached_data = await cache.aget('home_page_data')
    
    if cached_data:
        logger.info("Menggunakan data cache untuk halaman utama")
        return render(request, 'streamapp/index.html', context=cached_data)
    
    # Ambil data dari API
    try:
        # Ambil data home secara asinkron
        logger.info("Mengambil data home dari API")
        home_data = await asyncio.to_thread(get_home_data)
        
        # Buat context untuk template
        context = {
            'anime_terbaru': home_data.get('new_eps', []),
            'movie': home_data.get('movies', []),
            'anime_mingguan': home_data.get('top10', []),
            'jadwal_rilis': home_data.get('jadwal_rilis', {}),
            'days_of_week': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        }
        
        # Periksa apakah data yang diterima valid
        if not context['anime_terbaru'] and not context['movie'] and not context['anime_mingguan']:
            logger.warning("API mengembalikan data kosong untuk semua bagian")
            # Coba gunakan cache lama jika data kosong
            stale_cache = await cache.aget('stale_home_page_data')
            if stale_cache:
                logger.info("Menggunakan data cache lama untuk halaman utama")
                return render(request, 'streamapp/index.html', context=stale_cache)
    except Exception as e:
        logger.error(f"Error saat mengambil data home: {e}")
        # Coba gunakan cache lama jika terjadi error
        stale_cache = await cache.aget('stale_home_page_data')
        if stale_cache:
            logger.info("Menggunakan data cache lama untuk halaman utama")
            return render(request, 'streamapp/index.html', context=stale_cache)
        
        # Fallback ke data kosong jika tidak ada cache lama
        context = {
            'anime_terbaru': [],
            'movie': [],
            'anime_mingguan': [],
            'jadwal_rilis': {},
            'days_of_week': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            'error': f"Terjadi kesalahan saat memuat data: {e}"
        }
    
    # Cache hasil untuk 15 menit
    # Gunakan versioning untuk memudahkan invalidasi cache
    cache_version = int(time.time() / (60 * 15))  # Versi berubah setiap 15 menit
    await cache.aset(f'home_page_data_v{cache_version}', context, 60 * 15)
    
    # Simpan juga dengan kunci standar untuk kompatibilitas
    await cache.aset('home_page_data', context, 60 * 15)
    
    # Simpan sebagai cache lama untuk fallback
    await cache.aset('stale_home_page_data', context, 60 * 60 * 24 * 7)  # Simpan selama 7 hari
    
    return render(request, 'streamapp/index.html', context=context)

async def detail_anime(request, anime_slug=None):
    """
    View untuk menampilkan detail anime.
    """
    # Jika tidak ada anime_slug, kembalikan halaman kosong
    if not anime_slug:
        return render(request, 'streamapp/detail_anime.html', {})
    
    # Tambahkan logging untuk debug
    logger.info(f"Menerima request untuk anime_slug: {anime_slug}")
    
    try:
        # Periksa apakah anime_slug berisi URL yang tidak valid
        if ':' in anime_slug:
            # Jika anime_slug berisi karakter ':' (seperti https:v1.samehadaku.how...)
            # Ini menandakan URL yang tidak valid, coba perbaiki
            logger.warning(f"Mendeteksi URL tidak valid dengan ':': {anime_slug}")
            
            # Coba ekstrak bagian yang valid
            if 'v1.samehadaku.how' in anime_slug:
                # Jika berisi domain v1.samehadaku.how, ekstrak slug anime yang sebenarnya
                parts = anime_slug.split('how')
                if len(parts) > 1:
                    # Ambil bagian terakhir dari URL (slug anime)
                    anime_slug = parts[1].strip('/').split('/')[-1]
                    logger.info(f"Slug anime diperbaiki menjadi: {anime_slug}")
            else:
                # Jika format tidak dikenali, coba ekstrak bagian terakhir
                anime_slug = anime_slug.split('/')[-1]
                logger.info(f"Slug anime dibersihkan menjadi: {anime_slug}")
        
        # Dapatkan detail anime dengan caching
        anime_data = await get_anime_detail_data(anime_slug)
        
        # Jika data tidak ditemukan atau memiliki flag error, tampilkan pesan error
        if not anime_data:
            logger.warning(f"Data anime tidak ditemukan untuk slug: {anime_slug}")
            return render(request, 'streamapp/detail_anime.html', {'error': 'Anime tidak ditemukan'})
        
        # Periksa apakah data memiliki flag error
        if anime_data.get('error', False):
            logger.warning(f"Data anime memiliki flag error: {anime_data.get('message', 'Unknown error')}")
            return render(request, 'streamapp/detail_anime.html', {'error': anime_data.get('message', 'Terjadi kesalahan saat memuat data')})
        
        # Tambahkan thumbnail_url sebagai alias untuk url_cover jika belum ada
        if 'url_cover' in anime_data and anime_data['url_cover'] and not anime_data.get('thumbnail_url'):
            anime_data['thumbnail_url'] = anime_data['url_cover']
        
        # Pastikan semua field yang diperlukan ada
        required_fields = ['title', 'thumbnail_url', 'sinopsis', 'genres', 'details', 'episode_list']
        for field in required_fields:
            if field not in anime_data:
                logger.warning(f"Field {field} tidak ditemukan dalam data anime")
                if field == 'title':
                    anime_data[field] = f"Anime {anime_slug}"
                elif field == 'thumbnail_url':
                    anime_data[field] = "/static/images/placeholder.jpg"
                elif field == 'sinopsis':
                    anime_data[field] = "Tidak ada sinopsis tersedia."
                elif field == 'genres':
                    anime_data[field] = []
                elif field == 'details':
                    anime_data[field] = {}
                elif field == 'episode_list':
                    anime_data[field] = []
        
        # Render template dengan data anime
        context = {
            'anime': anime_data
        }
        
        return render(request, 'streamapp/detail_anime.html', context=context)
    
    except Exception as e:
        logger.error(f"Error saat mendapatkan detail anime: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return render(request, 'streamapp/detail_anime.html', {'error': f'Terjadi kesalahan saat memuat data: {str(e)}'})
    
    
@async_cache(ttl=60*15, prefix='all_anime_terbaru_')
async def get_all_anime_terbaru_data(page=1, max_pages=5):
    """
    Fungsi untuk mendapatkan data semua anime terbaru dengan caching.
    """
    # Gunakan asyncio.to_thread untuk menjalankan fungsi yang blocking di thread terpisah
    if page > 1:
        # Jika meminta halaman tertentu
        result = await asyncio.to_thread(get_anime_terbaru, page)
        
        # Log untuk debugging
        logger.info(f"Anime terbaru halaman {page}: {len(result)} item")
        
        # Pastikan result tidak None
        if result is None:
            result = []
        
        return {
            "current_page": page,
            "data": result,
            "total_pages": 5,  # Perkiraan jumlah halaman
            "anime_count": len(result)
        }
    else:
        # Jika meminta semua data dari beberapa halaman
        # Kumpulkan data dari beberapa halaman
        all_data = []
        for p in range(1, max_pages + 1):
            page_data = await asyncio.to_thread(get_anime_terbaru, p)
            
            # Log untuk debugging
            logger.info(f"Anime terbaru halaman {p}: {len(page_data) if page_data else 0} item")
            
            if not page_data:
                break
            all_data.extend(page_data)
        
        return {
            "current_page": 1,
            "total_pages": max_pages,
            "anime_count": len(all_data),
            "data": all_data
        }

async def all_list_anime_terbaru(request):
    """
    View untuk menampilkan semua anime terbaru dengan pagination.
    """
    # Ambil parameter page dari query string, default ke 1 jika tidak ada
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    # Ambil parameter max_pages dari query string, default ke 5 jika tidak ada
    max_pages = request.GET.get('max_pages', 5)
    try:
        max_pages = int(max_pages)
    except ValueError:
        max_pages = 5
    
    try:
        # Dapatkan data anime terbaru dengan caching
        anime_data = await get_all_anime_terbaru_data(page, max_pages)
        
        # Buat context untuk template
        context = {
            'anime_data': anime_data,
            'current_page': page,
            'max_pages': max_pages
        }
        
        return render(request, 'streamapp/all_list_anime_terbaru.html', context=context)
    
    except Exception as e:
        print(f"Error saat mendapatkan data anime terbaru: {e}")
        return render(request, 'streamapp/all_list_anime_terbaru.html', {'error': 'Terjadi kesalahan saat memuat data'})
    
    
    
@async_cache(ttl=60*60*3, prefix='jadwal_rilis_')  # Cache selama 3 jam
async def get_jadwal_rilis_data(day=None):
    """
    Fungsi untuk mendapatkan data jadwal rilis dengan caching.
    Jika day=None, ambil jadwal untuk semua hari.
    Jika day diisi, ambil jadwal untuk hari tertentu saja.
    """
    # Gunakan asyncio.to_thread untuk menjalankan fungsi yang blocking di thread terpisah
    try:
        result = await asyncio.to_thread(get_jadwal_rilis, day)
        
        if day:
            # Format hasil untuk konsistensi dengan format lama
            return {
                "day": day.capitalize(),
                "data": result
            }
        else:
            # Hasil sudah dalam format yang benar
            return result
    except Exception as e:
        logger.error(f"Error saat mendapatkan jadwal rilis: {e}")
        if day:
            return {"day": day.capitalize(), "data": []}
        else:
            return {}

async def all_list_jadwal_rilis(request):
    """
    View untuk menampilkan jadwal rilis anime.
    """
    # Ambil parameter day dari query string, default ke None jika tidak ada
    day = request.GET.get('day', None)
    
    try:
        # Dapatkan data jadwal rilis dengan caching
        jadwal_data = await get_jadwal_rilis_data(day)
        
        # Buat context untuk template
        context = {
            'jadwal_data': jadwal_data,
            'selected_day': day.capitalize() if day else None,
            'days_of_week': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        }
        
        return render(request, 'streamapp/all_list_jadwal_rilis.html', context=context)
    
    except Exception as e:
        print(f"Error saat mendapatkan data jadwal rilis: {e}")
        return render(request, 'streamapp/all_list_jadwal_rilis.html', {'error': 'Terjadi kesalahan saat memuat data'})
    

@async_cache(ttl=60*60*2, prefix='all_movie_')  # Cache selama 2 jam
async def get_all_movie_data(page=1):
    """
    Fungsi untuk mendapatkan data semua movie dengan caching.
    Menggunakan API client untuk mengambil data dari halaman khusus movie.
    """
    try:
        # Ambil data movie dari halaman yang diminta
        movie_data = await asyncio.to_thread(get_movie_list, page)
        
        # Log untuk debugging
        logger.info(f"Movie halaman {page}: {len(movie_data) if movie_data else 0} item")
        
        # Pastikan movie_data tidak None
        if movie_data is None:
            movie_data = []
        
        # Tambahkan anime_slug ke setiap movie jika belum ada
        for movie in movie_data:
            if not movie.get('anime_slug'):
                # Ekstrak anime_slug dari URL
                if movie.get('url', "N/A") != "N/A":
                    import re
                    anime_match = re.search(r'anime/([^/]+)', movie['url'])
                    if anime_match:
                        movie['anime_slug'] = anime_match.group(1)
        
        # Perkirakan jumlah halaman maksimal (karena API mungkin tidak menyediakan informasi ini)
        # Jika movie_data kosong, berarti kita sudah mencapai halaman terakhir
        max_pages = page if not movie_data else page + 1
        
        return {
            "current_page": page,
            "total_pages": max_pages,
            "movie_count": len(movie_data),
            "data": movie_data
        }
    except Exception as e:
        logger.error(f"Error saat mendapatkan data movie: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "current_page": page,
            "total_pages": 1,
            "movie_count": 0,
            "data": []
        }

async def all_list_movie(request):
    """
    View untuk menampilkan semua movie dengan pagination.
    """
    # Ambil parameter page dari query string, default ke 1 jika tidak ada
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    try:
        # Dapatkan data movie dengan caching
        movie_data = await get_all_movie_data(page)
        
        # Buat context untuk template
        context = {
            'movie_data': movie_data,
            'current_page': page
        }
        
        return render(request, 'streamapp/all_list_movie.html', context=context)
    
    except Exception as e:
        print(f"Error saat mendapatkan data movie: {e}")
        return render(request, 'streamapp/all_list_movie.html', {'error': 'Terjadi kesalahan saat memuat data'})
    
    
@async_cache(ttl=60*60*2, prefix='detail_episode_')  # Cache selama 2 jam
async def get_detail_episode_data(episode_url):
    """
    Fungsi untuk mendapatkan data detail episode dengan caching.
    """
    # Buat cache key yang unik untuk setiap episode_url
    cache_key = f"detail_episode_{episode_url.replace('/', '_')}"
    stale_cache_key = f"stale_detail_episode_{episode_url.replace('/', '_')}"
    
    # Cek cache terlebih dahulu
    cached_data = await cache.aget(cache_key)
    if cached_data:
        logger.info(f"Menggunakan data cache untuk episode: {episode_url}")
        return cached_data
    
    # Jika tidak ada di cache, ambil data baru
    try:
        # Gunakan asyncio.to_thread untuk menjalankan fungsi yang blocking di thread terpisah
        logger.info(f"Mengambil detail episode dari API: {episode_url}")
        result = await asyncio.to_thread(get_episode_detail, episode_url)
        
        # Simpan hasil ke cache
        if result:
            logger.info(f"Berhasil mendapatkan data episode: {episode_url}")
            await cache.aset(cache_key, result, 60*60*2)  # Cache selama 2 jam
            # Simpan juga sebagai cache lama untuk fallback
            await cache.aset(stale_cache_key, result, 60*60*24*7)  # Simpan selama 7 hari
            return result
        else:
            logger.warning(f"API mengembalikan data kosong untuk episode: {episode_url}")
            # Coba gunakan cache lama jika data kosong
            stale_cache = await cache.aget(stale_cache_key)
            if stale_cache:
                logger.info(f"Menggunakan data cache lama untuk episode: {episode_url}")
                return stale_cache
            return None
    except Exception as e:
        logger.error(f"Error saat mendapatkan detail episode: {e}")
        # Coba gunakan cache lama jika terjadi error
        stale_cache = await cache.aget(stale_cache_key)
        if stale_cache:
            logger.info(f"Menggunakan data cache lama untuk episode: {episode_url}")
            return stale_cache
        return None

# Fungsi sinkron untuk mendapatkan iklan aktif
def get_active_ads_sync(position=None):
    """
    Fungsi sinkron untuk mendapatkan iklan yang aktif berdasarkan posisi.
    """
    try:
        now = timezone.now()
        print(f"Current time: {now}")
        
        # Dapatkan semua iklan untuk debugging
        all_ads = list(Advertisement.objects.all())
        print(f"Total iklan di database: {len(all_ads)}")
        for ad in all_ads:
            print(f"Iklan: {ad.name}, Posisi: {ad.position}, Aktif: {ad.is_active}, Start: {ad.start_date}, End: {ad.end_date}")
        
        # Filter iklan yang aktif dan dalam rentang tanggal yang valid
        ads_query = Advertisement.objects.filter(is_active=True)
        print(f"Iklan aktif: {ads_query.count()}")
        
        # Filter berdasarkan tanggal mulai dan berakhir
        date_filtered = ads_query.filter(
            (models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)) &
            (models.Q(end_date__isnull=True) | models.Q(end_date__gte=now))
        )
        print(f"Iklan dalam rentang tanggal valid: {date_filtered.count()}")
        
        # Filter berdasarkan posisi jika ada
        if position:
            position_filtered = date_filtered.filter(position=position)
            print(f"Iklan untuk posisi {position}: {position_filtered.count()}")
        else:
            position_filtered = date_filtered
            print("Tidak ada filter posisi")
        
        # Urutkan berdasarkan prioritas (tinggi ke rendah)
        ordered_ads = position_filtered.order_by('-priority')
        
        # Konversi queryset ke list
        result = list(ordered_ads)
        print(f"Hasil akhir: {len(result)} iklan")
        for ad in result:
            print(f"Iklan hasil: {ad.name}, Posisi: {ad.position}")
        
        return result
    except Exception as e:
        print(f"Error saat mendapatkan iklan aktif: {e}")
        import traceback
        traceback.print_exc()
        return []

# Fungsi asinkron yang memanggil fungsi sinkron menggunakan sync_to_async
async def get_active_ads(position=None):
    """
    Fungsi asinkron untuk mendapatkan iklan yang aktif berdasarkan posisi.
    Menggunakan sync_to_async untuk memanggil fungsi sinkron dari konteks asinkron.
    """
    try:
        # Gunakan sync_to_async untuk memanggil fungsi sinkron dari konteks asinkron
        return await sync_to_async(get_active_ads_sync)(position)
    except Exception as e:
        print(f"Error saat mendapatkan iklan aktif (async): {e}")
        import traceback
        traceback.print_exc()
        return []

async def detail_episode_video(request, episode_slug=None):
    """
    View untuk menampilkan detail episode dengan video player.
    """
    if not episode_slug:
        logger.warning("Episode slug tidak diberikan")
        return render(request, 'streamapp/detail_episode_video.html', {'error': 'Episode tidak ditemukan'})
    
    try:
        # Tambahkan logging untuk debug
        logger.info(f"Menerima request untuk episode_slug: {episode_slug}")
        
        # Bangun URL lengkap dengan penanganan URL yang lebih baik
        # Periksa apakah episode_slug sudah berisi URL lengkap atau domain
        if episode_slug.startswith(('http://', 'https://')):
            # Jika episode_slug sudah berupa URL lengkap, gunakan langsung
            episode_url = episode_slug
            logger.info(f"Menggunakan URL lengkap dari slug: {episode_url}")
        elif ':' in episode_slug:
            # Jika episode_slug berisi karakter ':' (seperti https:v1.samehadaku.how...)
            # Ini menandakan URL yang tidak valid, coba perbaiki
            logger.warning(f"Mendeteksi URL tidak valid dengan ':': {episode_slug}")
            
            # Coba ekstrak bagian yang valid
            if 'v1.samehadaku.how' in episode_slug:
                # Jika berisi domain v1.samehadaku.how, gunakan domain tersebut
                # Pisahkan domain dan path dengan benar
                parts = episode_slug.replace('https:', 'https://').split('how')
                if len(parts) > 1:
                    domain = parts[0] + 'how'
                    path = parts[1]
                    # Pastikan ada garis miring (/) antara domain dan path
                    episode_url = f"{domain}/{path.lstrip('/')}"
                else:
                    # Fallback jika pemisahan gagal
                    episode_url = episode_slug.replace('https:', 'https://')
                
                logger.info(f"URL diperbaiki menjadi: {episode_url}")
            else:
                # Jika format tidak dikenali, gunakan base_url default
                base_url = "https://v1.samehadaku.how/"
                # Hapus bagian yang mungkin berisi protokol tidak valid
                clean_slug = episode_slug.split(':')[-1]
                episode_url = f"{base_url}{clean_slug}/"
                logger.info(f"URL dibersihkan menjadi: {episode_url}")
        else:
            # Jika episode_slug adalah slug biasa, gunakan base_url
            base_url = "https://v1.samehadaku.how/"
            episode_url = f"{base_url}{episode_slug}/"
            logger.info(f"URL dibangun dengan base_url: {episode_url}")
        
        # Dapatkan data detail episode dengan caching
        episode_data = await get_detail_episode_data(episode_url)
        
        # Jika data tidak ditemukan, kembalikan halaman kosong
        if not episode_data:
            logger.warning(f"Data episode tidak ditemukan untuk URL: {episode_url}")
            return render(request, 'streamapp/detail_episode_video.html', {
                'error': 'Episode tidak ditemukan',
                'episode_url': episode_url
            })
        
        # Dapatkan iklan yang aktif untuk berbagai posisi
        ads = {}
        debug_info = {
            'has_advertisement_model': 'Advertisement' in globals(),
            'positions': [],
            'ads_found': {},
            'errors': []
        }
        
        try:
            # Hanya coba dapatkan iklan jika model Advertisement ada
            if 'Advertisement' in globals():
                logger.info("Model Advertisement ditemukan, mencoba mendapatkan iklan")
                positions = [pos[0] for pos in Advertisement.POSITION_CHOICES]
                debug_info['positions'] = positions
                logger.debug(f"Posisi iklan yang tersedia: {positions}")
                
                # Dapatkan semua iklan untuk debugging (menggunakan sync_to_async)
                all_ads = await sync_to_async(list)(Advertisement.objects.all())
                debug_info['total_ads'] = len(all_ads)
                debug_info['all_ads'] = [{'name': ad.name, 'position': ad.position, 'is_active': ad.is_active} for ad in all_ads]
                
                for position in positions:
                    logger.debug(f"Mencoba mendapatkan iklan untuk posisi: {position}")
                    position_ads = await get_active_ads(position)
                    debug_info['ads_found'][position] = len(position_ads)
                    
                    if position_ads:
                        # Ambil iklan dengan prioritas tertinggi untuk posisi ini
                        ads[position] = position_ads[0]
                        logger.info(f"Iklan ditemukan untuk posisi {position}: {position_ads[0].name}")
                    else:
                        logger.debug(f"Tidak ada iklan untuk posisi {position}")
                
                logger.info(f"Total iklan yang akan ditampilkan: {len(ads)}")
            else:
                logger.warning("Model Advertisement tidak ditemukan")
                debug_info['errors'].append("Model Advertisement tidak ditemukan")
        except Exception as ad_error:
            logger.error(f"Error saat mendapatkan iklan: {ad_error}")
            import traceback
            logger.error(traceback.format_exc())
            debug_info['errors'].append(str(ad_error))
            # Jika ada error dengan iklan, tetap lanjutkan tanpa iklan
            ads = {}
        
        # Pastikan episode_data memiliki semua field yang diperlukan
        if not episode_data.get('navigation'):
            episode_data['navigation'] = {}
        
        if not episode_data.get('anime_info'):
            episode_data['anime_info'] = {}
        
        if not episode_data.get('other_episodes'):
            episode_data['other_episodes'] = []
        
        # Pastikan semua video_urls ada dan valid
        if not episode_data.get('video_urls') or not isinstance(episode_data['video_urls'], list):
            episode_data['video_urls'] = []
            logger.warning(f"Data video_urls tidak valid untuk episode: {episode_url}")
        
        # Render template dengan data episode, iklan, dan debug info
        context = {
            'episode': episode_data,
            'ads': ads,
            'debug_info': debug_info
        }
        
        return render(request, 'streamapp/detail_episode_video.html', context=context)
    
    except Exception as e:
        logger.error(f"Error saat mendapatkan detail episode: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return render(request, 'streamapp/detail_episode_video.html', {
            'error': 'Terjadi kesalahan saat memuat data',
            'error_detail': str(e),
            'episode_slug': episode_slug
        })

@async_cache(ttl=60*5, prefix='search_')  # Cache selama 5 menit
async def get_search_results(query, max_results=20):
    """
    Fungsi untuk mencari anime berdasarkan query dengan caching.
    """
    # Buat cache key yang unik untuk setiap query
    cache_key = f"search_{query.replace(' ', '_')}"
    
    # Cek cache terlebih dahulu
    cached_data = await cache.aget(cache_key)
    if cached_data:
        return cached_data
    
    # Jika tidak ada di cache, lakukan pencarian menggunakan API client
    try:
        # Gunakan asyncio.to_thread untuk menjalankan fungsi yang blocking di thread terpisah
        search_results = await asyncio.to_thread(search_anime, query)
        
        # Batasi jumlah hasil jika diperlukan
        if search_results and len(search_results) > max_results:
            search_results = search_results[:max_results]
        
        # Tambahkan anime_slug ke setiap hasil jika search_results tidak None
        if search_results:
            for result in search_results:
                # Ekstrak anime_slug dari URL
                import re
                anime_slug = ""
                if result.get('url_anime', "N/A") != "N/A":
                    anime_match = re.search(r'anime/([^/]+)', result['url_anime'])
                    if anime_match:
                        result['anime_slug'] = anime_match.group(1)
                    else:
                        result['anime_slug'] = ""
        
        # Simpan hasil ke cache
        await cache.aset(cache_key, search_results, 60*5)  # Cache selama 5 menit
        
        return search_results
    
    except Exception as e:
        logger.error(f"Error saat melakukan pencarian: {e}")
        return []

async def search(request):
    """
    View untuk menampilkan hasil pencarian.
    """
    # Ambil parameter query dari query string
    query = request.GET.get('q', '')
    
    # Jika query kosong, kembalikan halaman kosong
    if not query:
        return render(request, 'streamapp/search_results.html', {'query': query, 'results': []})
    
    try:
        # Dapatkan hasil pencarian dengan caching dan multi-threading
        search_results = await get_search_results(query)
        
        # Buat context untuk template
        context = {
            'query': query,
            'results': search_results if search_results else [],
            'result_count': len(search_results) if search_results else 0
        }
        
        return render(request, 'streamapp/search_results.html', context=context)
    
    except Exception as e:
        print(f"Error saat menampilkan hasil pencarian: {e}")
        return render(request, 'streamapp/search_results.html', {'query': query, 'error': 'Terjadi kesalahan saat memuat data'})

async def user_collection(request):
    """
    View untuk menampilkan koleksi pengguna (watchlist, favorites, dan watch history).
    Data disimpan di localStorage di sisi klien, jadi view ini hanya menampilkan template.
    """
    try:
        # Render template tanpa data khusus
        return render(request, 'streamapp/user_collection.html')
    except Exception as e:
        print(f"Error saat menampilkan koleksi pengguna: {e}")
        return HttpResponse("Terjadi kesalahan saat memuat halaman koleksi pengguna", status=500)