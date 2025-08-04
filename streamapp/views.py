from django.shortcuts import render
from django.http import HttpResponse
from django.core.cache import cache
import asyncio
import time
import functools
import concurrent.futures
from .models import Advertisement
from .models import Advertisement, SiteConfiguration # Tambahkan SiteConfiguration
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
    get_current_api_info,
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
async def get_anime_terbaru_data(page=1):
    """
    Fungsi untuk mendapatkan data anime terbaru dengan caching.
    """
    result = await asyncio.to_thread(get_anime_terbaru, page)
    
    # Jika hasil None atau empty list, kembalikan list kosong
    if not result:
        logger.warning(f"Hasil anime terbaru kosong untuk halaman {page}")
        return []
    
    # Periksa apakah hasil memiliki struktur baru dengan confidence score
    if isinstance(result, dict) and 'confidence_score' in result and 'data' in result:
        confidence = result.get('confidence_score', 0)
        logger.info(f"Mendapatkan data anime terbaru dengan confidence score: {confidence}")
        
        # Periksa apakah data kosong
        if not result.get('data'):
            logger.warning(f"Data anime terbaru kosong meskipun API merespons dengan confidence score: {confidence}")
            return []
            
        return result['data']
    
    # Jika tidak, kembalikan hasil langsung (kompatibilitas dengan struktur lama)
    # Pastikan hasil adalah list
    if not isinstance(result, list):
        logger.warning(f"Hasil anime terbaru bukan list: {type(result)}")
        if isinstance(result, dict):
            # Coba ekstrak data jika ada
            return result.get('data', []) if result.get('data') else []
        return []
        
    return result

# Fungsi untuk mendapatkan data movie dengan caching
async def get_movie_data(page=1):
    """
    Fungsi untuk mendapatkan data movie dengan caching.
    """
    result = await asyncio.to_thread(get_movie_list, page)
    
    # Jika hasil None atau empty list, kembalikan list kosong
    if not result:
        logger.warning(f"Hasil movie kosong untuk halaman {page}")
        return []
    
    # Periksa apakah hasil memiliki struktur baru dengan confidence score
    if isinstance(result, dict) and 'confidence_score' in result and 'data' in result:
        confidence = result.get('confidence_score', 0)
        logger.info(f"Mendapatkan data movie dengan confidence score: {confidence}")
        
        # Periksa apakah data kosong
        if not result.get('data'):
            logger.warning(f"Data movie kosong meskipun API merespons dengan confidence score: {confidence}")
            return []
            
        return result['data']
    
    # Jika tidak, kembalikan hasil langsung (kompatibilitas dengan struktur lama)
    # Pastikan hasil adalah list
    if not isinstance(result, list):
        logger.warning(f"Hasil movie bukan list: {type(result)}")
        if isinstance(result, dict):
            # Coba ekstrak data jika ada
            return result.get('data', []) if result.get('data') else []
        return []
        
    return result


# Fungsi untuk mendapatkan data anime mingguan dengan caching
async def get_anime_mingguan_data():
    """
    Fungsi untuk mendapatkan data anime mingguan dengan caching.
    """
    try:
        # Coba ambil dari get_home_data terlebih dahulu
        home_data = await asyncio.to_thread(get_home_data)
        
        # Jika hasil None atau empty dict, lanjutkan ke fallback
        if not home_data:
            logger.warning("Data home kosong, mencoba API fallback")
            raise Exception("Data home kosong")
        
        # Periksa apakah hasil memiliki struktur baru dengan confidence score
        if isinstance(home_data, dict) and 'confidence_score' in home_data and 'data' in home_data:
            confidence = home_data.get('confidence_score', 0)
            logger.info(f"Mendapatkan data home dengan confidence score: {confidence}")
            
            # Periksa apakah data kosong
            if not home_data.get('data'):
                logger.warning(f"Data home kosong meskipun API merespons dengan confidence score: {confidence}")
                raise Exception("Data home kosong meskipun API merespons")
                
            home_data = home_data['data']
        
        # Periksa apakah home_data adalah dictionary
        if not isinstance(home_data, dict):
            logger.warning(f"Data home bukan dictionary: {type(home_data)}")
            raise Exception(f"Data home bukan dictionary: {type(home_data)}")
        
        # Periksa apakah top10 ada dan tidak kosong
        if "top10" in home_data and home_data["top10"]:
            logger.info(f"Berhasil mendapatkan data anime mingguan dari get_home_data: {len(home_data['top10'])} item")
            return home_data.get("top10", [])
        else:
            logger.warning("Data anime mingguan kosong dari get_home_data, mencoba API fallback")
            # Jika data kosong, coba ambil dari API fallback
            # Untuk saat ini, kita tidak memiliki endpoint khusus untuk anime mingguan,
            # jadi kita gunakan data anime terbaru sebagai fallback
            anime_terbaru = await get_anime_terbaru_data()
            if anime_terbaru:
                logger.info(f"Menggunakan data anime terbaru sebagai fallback untuk anime mingguan: {len(anime_terbaru)} item")
                return anime_terbaru[:10]  # Ambil 10 anime terbaru sebagai fallback
            else:
                logger.warning("Gagal mendapatkan data anime mingguan dari semua sumber")
                return []
    except Exception as e:
        logger.error(f"Error saat mendapatkan data anime mingguan: {e}")
        # Coba ambil dari API fallback
        try:
            anime_terbaru = await get_anime_terbaru_data()
            if anime_terbaru:
                logger.info(f"Menggunakan data anime terbaru sebagai fallback untuk anime mingguan: {len(anime_terbaru)} item")
                return anime_terbaru[:10]  # Ambil 10 anime terbaru sebagai fallback
        except Exception as e2:
            logger.error(f"Error saat mendapatkan data anime terbaru sebagai fallback: {e2}")
        return []

# Fungsi untuk mengambil data setiap bagian secara terpisah
async def _fetch_individual_sections(context):
    """
    Fungsi untuk mengambil data untuk setiap bagian secara terpisah.
    Digunakan sebagai fallback ketika get_home_data gagal.
    
    Args:
        context: Dictionary context yang akan diperbarui dengan data yang berhasil diambil
    """
    logger.info("Mengambil data untuk setiap bagian secara terpisah")
    
    # Ambil data anime terbaru
    try:
        logger.info("Mengambil data anime terbaru")
        anime_terbaru = await get_anime_terbaru_data()
        if anime_terbaru:
            context['anime_terbaru'] = anime_terbaru
            logger.info(f"Berhasil mendapatkan {len(anime_terbaru)} anime terbaru")
    except Exception as e:
        logger.error(f"Error saat mengambil data anime terbaru: {e}")
    
    # Ambil data movie
    try:
        logger.info("Mengambil data movie")
        movie_data = await get_movie_data()
        if movie_data:
            context['movie'] = movie_data
            logger.info(f"Berhasil mendapatkan {len(movie_data)} movie")
    except Exception as e:
        logger.error(f"Error saat mengambil data movie: {e}")
    
    # Ambil data jadwal rilis
    try:
        logger.info("Mengambil data jadwal rilis")
        jadwal_data = await get_jadwal_rilis_data()
        if jadwal_data:
            context['jadwal_rilis'] = jadwal_data
            if isinstance(jadwal_data, dict):
                logger.info(f"Berhasil mendapatkan jadwal rilis untuk {len(jadwal_data.keys())} hari")
            else:
                logger.info(f"Berhasil mendapatkan jadwal rilis")
    except Exception as e:
        logger.error(f"Error saat mengambil data jadwal rilis: {e}")
    
    # Ambil data anime mingguan
    try:
        logger.info("Mengambil data anime mingguan")
        anime_mingguan = await get_anime_mingguan_data()
        if anime_mingguan:
            context['anime_mingguan'] = anime_mingguan
            logger.info(f"Berhasil mendapatkan {len(anime_mingguan)} anime mingguan")
    except Exception as e:
        logger.error(f"Error saat mengambil data anime mingguan: {e}")
    
    # Periksa apakah berhasil mendapatkan data
    if context['anime_terbaru'] or context['movie'] or context['anime_mingguan'] or context['jadwal_rilis']:
        logger.info("Berhasil mendapatkan beberapa data dari API fallback")
    else:
        logger.warning("Gagal mendapatkan data dari semua API")
        context['error'] = "Terjadi kesalahan saat memuat data. Silakan coba lagi nanti."

def _transform_anime_detail_data(raw_data: dict, anime_slug: str) -> dict:
    """
    Transforms raw API data into the structure expected by the template.
    """
    if not raw_data or not isinstance(raw_data, dict):
        return {
            "error": True,
            "message": f"Data anime tidak valid atau kosong untuk slug: {anime_slug}",
            "title": f"Anime {anime_slug}",
            "thumbnail_url": "/static/img/kortekstream-logo.png",
            "url_cover": "/static/img/kortekstream-logo.png",
            "sinopsis": "Data anime tidak ditemukan.",
            "genres": [],
            "details": {},
            "episode_list": []
        }

    # Coba dapatkan cover image dari berbagai sumber
    cover_url = raw_data.get('url_cover')
    
    # Jika url_cover adalah placeholder, coba ambil dari recommendations
    if cover_url and 'placeholder' in cover_url and raw_data.get('recommendations'):
        for rec in raw_data.get('recommendations', []):
            if rec.get('cover_url') and 'placeholder' not in rec.get('cover_url', ''):
                cover_url = rec.get('cover_url')
                break
    
    # Jika masih tidak ada, gunakan default
    if not cover_url or 'placeholder' in cover_url:
        cover_url = "/static/img/kortekstream-logo.png"
    
    return {
        "title": raw_data.get('judul', f"Anime {anime_slug}"),
        "thumbnail_url": cover_url,
        "url_cover": cover_url,
        "sinopsis": raw_data.get('sinopsis', "Sinopsis tidak tersedia."),
        "genres": raw_data.get('genre', []) or raw_data.get('genres', []),
        "details": raw_data.get('details', {}),
        "episode_list": raw_data.get('episode_list', []),
        "recommendations": raw_data.get('recommendations', []),
        "error": raw_data.get('error', False),
        "message": raw_data.get('message', ''),
        "rating": raw_data.get('rating', {'score': 'N/A', 'users': 'N/A'})
    }

# Fungsi untuk mendapatkan detail anime dengan caching
async def get_anime_detail_data(anime_slug):
    """
    Fungsi untuk mendapatkan detail anime dengan caching.
    """
    logger.info(f"Mengambil detail anime: {anime_slug}")
    
    try:
        get_anime_detail_async = sync_to_async(get_anime_detail)
        raw_result = await get_anime_detail_async(anime_slug)
        
        # Transform the data to the expected structure
        transformed_result = _transform_anime_detail_data(raw_result, anime_slug)
        
        if not transformed_result.get('error'):
            logger.info(f"Berhasil mendapatkan dan mentransformasi data anime: {anime_slug}")
            # Cache the transformed result
            await cache.aset(f"anime_detail_{anime_slug}", transformed_result, 60*60*24)
            return transformed_result
        else:
            logger.warning(f"Gagal mendapatkan data valid untuk anime: {anime_slug}. Pesan: {transformed_result.get('message')}")
            return transformed_result

    except Exception as e:
        logger.error(f"Error saat mengambil detail anime {anime_slug}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return _transform_anime_detail_data({}, anime_slug) # Return a default error structure

# Create your views here.
async def index(request):
    """
    View untuk halaman utama.
    """
    response = None
    try:
        # Ambil data dari API
        logger.info("Mengambil data home dari API")
        home_data = await asyncio.to_thread(get_home_data)
        
        # Periksa apakah hasil memiliki struktur baru dengan confidence score
        if isinstance(home_data, dict) and 'confidence_score' in home_data:
            confidence = home_data.get('confidence_score', 0)
            logger.info(f"Mendapatkan data home dengan confidence score: {confidence}")
            
            # Jika ada field 'data', gunakan itu (gomunime format)
            if 'data' in home_data:
                if not home_data.get('data'):
                    logger.warning(f"Data home kosong meskipun API merespons dengan confidence score: {confidence}")
                    raise Exception("Data home kosong meskipun API merespons")
                home_data = home_data['data']
            # Jika tidak ada field 'data', gunakan data langsung (samehadaku format)
            else:
                logger.info("Menggunakan data langsung dari API (samehadaku format)")
        
        # Periksa apakah home_data adalah dictionary
        if not isinstance(home_data, dict):
            logger.warning(f"Data home bukan dictionary: {type(home_data)}")
            raise Exception(f"Data home bukan dictionary: {type(home_data)}")
        
        # Buat context untuk template
        context = {
            'anime_terbaru': home_data.get('new_eps', []),
            'movie': home_data.get('movies', []),
            'anime_mingguan': home_data.get('top10', []),
            'jadwal_rilis': home_data.get('jadwal_rilis', {}),
            'days_of_week': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        }
        
        # Log jumlah item yang diterima untuk debugging
        logger.info(f"Data diterima - Anime Terbaru: {len(context['anime_terbaru'])}, " +
                   f"Movie: {len(context['movie'])}, " +
                   f"Anime Mingguan: {len(context['anime_mingguan'])}, " +
                   f"Jadwal Rilis: {len(context['jadwal_rilis'].keys()) if isinstance(context['jadwal_rilis'], dict) else 0}")
        
        # Periksa apakah data yang diterima valid
        if not context['anime_terbaru'] and not context['movie'] and not context['anime_mingguan']:
            logger.warning("API mengembalikan data kosong untuk semua bagian")
            await _fetch_individual_sections(context)

        response = render(request, 'streamapp/index.html', context=context)

    except Exception as e:
        logger.error(f"Error saat mengambil data home: {e}")
        context = {
            'anime_terbaru': [],
            'movie': [],
            'anime_mingguan': [],
            'jadwal_rilis': {},
            'days_of_week': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            'error': "Terjadi kesalahan saat memuat data. Silakan coba lagi nanti."
        }
        await _fetch_individual_sections(context)
        response = render(request, 'streamapp/index.html', context=context)
    
    # Set Cache-Control header to prevent browser caching
    if response:
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

    return response

async def detail_anime(request, anime_slug=None):
    """
    View untuk menampilkan detail anime.
    """
    response = None
    # Jika tidak ada anime_slug, kembalikan halaman kosong
    if not anime_slug:
        response = render(request, 'streamapp/detail_anime.html', {})
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
    
    # Tambahkan logging untuk debug
    logger.info(f"Menerima request untuk anime_slug: {anime_slug}")
    
    try:
        # Dapatkan detail anime
        anime_data = await get_anime_detail_data(anime_slug)
        
        # Jika data tidak ditemukan atau memiliki flag error, tampilkan pesan error
        if not anime_data or anime_data.get('error', False):
            logger.warning(f"Data anime tidak ditemukan atau error untuk slug: {anime_slug}")
            context = {'error': anime_data.get('message', 'Anime tidak ditemukan') if anime_data else 'Anime tidak ditemukan'}
            response = render(request, 'streamapp/detail_anime.html', context)
        else:
            # Pastikan semua field yang diperlukan ada
            # ... (logika untuk memastikan field ada)
            context = {'anime': anime_data}
            response = render(request, 'streamapp/detail_anime.html', context=context)
    
    except Exception as e:
        logger.error(f"Error saat mendapatkan detail anime: {e}")
        context = {'error': f'Terjadi kesalahan saat memuat data: {str(e)}'}
        response = render(request, 'streamapp/detail_anime.html', context)
    
    # Set Cache-Control header to prevent browser caching
    if response:
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

    return response
    
    
async def get_all_anime_terbaru_data(page=1, max_pages=5):
    """
    Fungsi untuk mendapatkan data semua anime terbaru dengan caching.
    """
    # Gunakan asyncio.to_thread untuk menjalankan fungsi yang blocking di thread terpisah
    if page > 1:
        # Jika meminta halaman tertentu
        result = await asyncio.to_thread(get_anime_terbaru, page)
        
        # Periksa apakah hasil memiliki struktur baru dengan confidence score
        if isinstance(result, dict) and 'confidence_score' in result:
            confidence = result.get('confidence_score', 0)
            logger.info(f"Mendapatkan data anime terbaru halaman {page} dengan confidence score: {confidence}")
            
            # Jika ada field 'data', gunakan itu (gomunime format)
            if 'data' in result:
                result = result['data']
            # Jika tidak ada field 'data', gunakan data langsung (samehadaku format)
            else:
                logger.info("Menggunakan data langsung dari API (samehadaku format)")
        
        # Log untuk debugging
        logger.info(f"Anime terbaru halaman {page}: {len(result) if result else 0} item")
        
        # Pastikan result tidak None
        if result is None:
            result = []
        
        # Proses data untuk memastikan anime_slug ada
        processed_data = []
        for anime in result:
            # Periksa apakah anime adalah dictionary
            if not isinstance(anime, dict):
                logger.error(f"Data anime bukan dictionary: {anime}")
                continue
                
            # Tambahkan anime_slug jika belum ada
            if not anime.get('anime_slug'):
                # Ekstrak anime_slug dari URL
                if anime.get('url', "N/A") != "N/A":
                    import re
                    anime_match = re.search(r'anime/([^/]+)', anime['url'])
                    if anime_match:
                        anime['anime_slug'] = anime_match.group(1)
                    else:
                        # Jika tidak bisa ekstrak dari URL, gunakan judul sebagai fallback
                        if anime.get('judul'):
                            import re
                            # Buat slug dari judul
                            slug = re.sub(r'[^a-zA-Z0-9]', '-', anime.get('judul', '')).lower()
                            slug = re.sub(r'-+', '-', slug).strip('-')
                            anime['anime_slug'] = slug
                        else:
                            # Jika tidak ada judul, gunakan placeholder
                            anime['anime_slug'] = 'unknown-anime'
            
            processed_data.append(anime)
        
        return {
            "current_page": page,
            "data": processed_data,
            "total_pages": 5,  # Perkiraan jumlah halaman
            "anime_count": len(processed_data)
        }
    else:
        # Jika meminta semua data dari beberapa halaman
        # Kumpulkan data dari beberapa halaman
        all_data = []
        for p in range(1, max_pages + 1):
            page_data = await asyncio.to_thread(get_anime_terbaru, p)
            
            # Periksa apakah hasil memiliki struktur baru dengan confidence score
            if isinstance(page_data, dict) and 'confidence_score' in page_data:
                confidence = page_data.get('confidence_score', 0)
                logger.info(f"Mendapatkan data anime terbaru halaman {p} dengan confidence score: {confidence}")
                
                # Jika ada field 'data', gunakan itu (gomunime format)
                if 'data' in page_data:
                    page_data = page_data['data']
                # Jika tidak ada field 'data', gunakan data langsung (samehadaku format)
                else:
                    logger.info("Menggunakan data langsung dari API (samehadaku format)")
            
            # Log untuk debugging
            logger.info(f"Anime terbaru halaman {p}: {len(page_data) if page_data else 0} item")
            
            if not page_data:
                break
                
            # Proses data untuk memastikan anime_slug ada
            for anime in page_data:
                # Periksa apakah anime adalah dictionary
                if not isinstance(anime, dict):
                    logger.error(f"Data anime bukan dictionary: {anime}")
                    continue
                    
                # Tambahkan anime_slug jika belum ada
                if not anime.get('anime_slug'):
                    # Ekstrak anime_slug dari URL
                    if anime.get('url', "N/A") != "N/A":
                        import re
                        anime_match = re.search(r'anime/([^/]+)', anime['url'])
                        if anime_match:
                            anime['anime_slug'] = anime_match.group(1)
                        else:
                            # Jika tidak bisa ekstrak dari URL, gunakan judul sebagai fallback
                            if anime.get('judul'):
                                import re
                                # Buat slug dari judul
                                slug = re.sub(r'[^a-zA-Z0-9]', '-', anime.get('judul', '')).lower()
                                slug = re.sub(r'-+', '-', slug).strip('-')
                                anime['anime_slug'] = slug
                            else:
                                # Jika tidak ada judul, gunakan placeholder
                                anime['anime_slug'] = 'unknown-anime'
                
                all_data.append(anime)
        
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
    response = None
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
        # Dapatkan data anime terbaru
        anime_data = await get_all_anime_terbaru_data(page, max_pages)
        
        # Buat context untuk template
        context = {
            'anime_data': anime_data,
            'current_page': page,
            'max_pages': max_pages
        }
        
        response = render(request, 'streamapp/all_list_anime_terbaru.html', context=context)
    
    except Exception as e:
        print(f"Error saat mendapatkan data anime terbaru: {e}")
        context = {'error': 'Terjadi kesalahan saat memuat data'}
        response = render(request, 'streamapp/all_list_anime_terbaru.html', context)

    # Set Cache-Control header to prevent browser caching
    if response:
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

    return response
    
    
    
async def get_jadwal_rilis_data(day=None):
    """
    Fungsi untuk mendapatkan data jadwal rilis dengan caching.
    Jika day=None, ambil jadwal untuk semua hari.
    Jika day diisi, ambil jadwal untuk hari tertentu saja.
    """
    # Gunakan asyncio.to_thread untuk menjalankan fungsi yang blocking di thread terpisah
    try:
        result = await asyncio.to_thread(get_jadwal_rilis, day)
        
        # Periksa apakah hasil memiliki struktur baru dengan confidence score
        if isinstance(result, dict) and 'confidence_score' in result:
            confidence = result.get('confidence_score', 0)
            logger.info(f"Mendapatkan data jadwal rilis dengan confidence score: {confidence}")
            
            # Jika ada field 'data', gunakan itu (gomunime format)
            if 'data' in result:
                result = result['data']
            # Jika tidak ada field 'data', gunakan data langsung (samehadaku format)
            else:
                logger.info("Menggunakan data langsung dari API (samehadaku format)")
        
        # Validasi hasil
        if result is None:
            logger.warning("Hasil jadwal rilis adalah None")
            if day:
                return {"day": day.capitalize(), "data": []}
            else:
                return {}
        
        # Periksa tipe data hasil
        if not isinstance(result, (dict, list)):
            logger.error(f"Hasil jadwal rilis bukan dictionary atau list: {type(result)}")
            if day:
                return {"day": day.capitalize(), "data": []}
            else:
                # Buat dictionary kosong untuk semua hari
                empty_result = {}
                for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                    empty_result[d] = []
                return empty_result
        
        if day:
            # Format hasil untuk konsistensi dengan format lama
            # Pastikan data adalah list
            if not isinstance(result, list):
                logger.warning(f"Hasil jadwal rilis untuk hari {day} bukan list: {type(result)}")
                result = []
                
            return {
                "day": day.capitalize(),
                "data": result
            }
        else:
            # Hasil seharusnya dictionary
            if not isinstance(result, dict):
                logger.warning(f"Hasil jadwal rilis untuk semua hari bukan dictionary: {type(result)}")
                # Buat dictionary kosong untuk semua hari
                empty_result = {}
                for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                    empty_result[d] = []
                return empty_result
                
            # Pastikan semua nilai dalam dictionary adalah list
            for key, value in result.items():
                if not isinstance(value, list):
                    logger.warning(f"Nilai untuk hari {key} bukan list: {type(value)}")
                    result[key] = []
                    
            return result
    except Exception as e:
        logger.error(f"Error saat mendapatkan jadwal rilis: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        if day:
            return {"day": day.capitalize(), "data": []}
        else:
            # Buat dictionary kosong untuk semua hari
            empty_result = {}
            for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                empty_result[d] = []
            return empty_result

async def all_list_jadwal_rilis(request):
    """
    View untuk menampilkan jadwal rilis anime.
    """
    response = None
    # Ambil parameter day dari query string, default ke None jika tidak ada
    day = request.GET.get('day', None)
    
    try:
        # Dapatkan data jadwal rilis
        jadwal_data = await get_jadwal_rilis_data(day)
        
        # Buat context untuk template
        context = {
            'jadwal_data': jadwal_data,
            'selected_day': day.capitalize() if day else None,
            'days_of_week': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        }
        
        response = render(request, 'streamapp/all_list_jadwal_rilis.html', context=context)
    
    except Exception as e:
        print(f"Error saat mendapatkan data jadwal rilis: {e}")
        context = {'error': 'Terjadi kesalahan saat memuat data'}
        response = render(request, 'streamapp/all_list_jadwal_rilis.html', context)

    # Set Cache-Control header to prevent browser caching
    if response:
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

    return response
    

async def get_all_movie_data(page=1):
    """
    Fungsi untuk mendapatkan data semua movie dengan caching.
    Menggunakan API client untuk mengambil data dari halaman khusus movie.
    """
    try:
        # Ambil data movie dari halaman yang diminta
        movie_data = await asyncio.to_thread(get_movie_list, page)
        
        # Periksa apakah hasil memiliki struktur baru dengan confidence score
        if isinstance(movie_data, dict) and 'confidence_score' in movie_data:
            confidence = movie_data.get('confidence_score', 0)
            logger.info(f"Mendapatkan data movie halaman {page} dengan confidence score: {confidence}")
            
            # Jika ada field 'data', gunakan itu (gomunime format)
            if 'data' in movie_data:
                movie_data = movie_data['data']
            # Jika tidak ada field 'data', gunakan data langsung (samehadaku format)
            else:
                logger.info("Menggunakan data langsung dari API (samehadaku format)")
        
        # Log untuk debugging
        logger.info(f"Movie halaman {page}: {len(movie_data) if movie_data else 0} item")
        
        # Pastikan movie_data tidak None
        if movie_data is None:
            movie_data = []
        
        # Tambahkan anime_slug ke setiap movie jika belum ada
        processed_movie_data = []
        for movie in movie_data:
            # Periksa apakah movie adalah dictionary
            if not isinstance(movie, dict):
                logger.error(f"Data movie bukan dictionary: {movie}")
                continue
                
            # Tambahkan anime_slug jika belum ada
            if not movie.get('anime_slug'):
                # Ekstrak anime_slug dari URL
                if movie.get('url', "N/A") != "N/A":
                    import re
                    anime_match = re.search(r'anime/([^/]+)', movie['url'])
                    if anime_match:
                        movie['anime_slug'] = anime_match.group(1)
                    else:
                        # Jika tidak bisa ekstrak dari URL, gunakan judul sebagai fallback
                        if movie.get('judul'):
                            import re
                            # Buat slug dari judul
                            slug = re.sub(r'[^a-zA-Z0-9]', '-', movie.get('judul', '')).lower()
                            slug = re.sub(r'-+', '-', slug).strip('-')
                            movie['anime_slug'] = slug
                        else:
                            # Jika tidak ada judul, gunakan placeholder
                            movie['anime_slug'] = 'unknown-movie'
            
            processed_movie_data.append(movie)
        
        # Gunakan data yang sudah diproses
        movie_data = processed_movie_data
        
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
    response = None
    # Ambil parameter page dari query string, default ke 1 jika tidak ada
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    try:
        # Dapatkan data movie
        movie_data = await get_all_movie_data(page)
        
        # Buat context untuk template
        context = {
            'movie_data': movie_data,
            'current_page': page
        }
        
        response = render(request, 'streamapp/all_list_movie.html', context=context)
    
    except Exception as e:
        print(f"Error saat mendapatkan data movie: {e}")
        context = {'error': 'Terjadi kesalahan saat memuat data'}
        response = render(request, 'streamapp/all_list_movie.html', context)

    # Set Cache-Control header to prevent browser caching
    if response:
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

    return response
    
    
def _transform_episode_detail_data(raw_data: dict, episode_url: str) -> dict:
    """
    Transforms raw episode data into the structure expected by the template.
    """
    logger.info(f"Raw episode data received for {episode_url}: {raw_data}")
    if not raw_data or not isinstance(raw_data, dict):
        return {
            "error": True,
            "message": f"Data episode tidak valid atau kosong untuk URL: {episode_url}",
            "title": "Episode Tidak Ditemukan",
            "anime_info": {},
            "navigation": {},
            "video_urls": [],
            "download_links": [],
            "other_episodes": []
        }

    return {
        "title": raw_data.get('judul_episode') or raw_data.get('title', "Judul Episode Tidak Tersedia"),
        "anime_info": raw_data.get('anime_info', {}),
        "navigation": raw_data.get('navigation', {}),
        "streaming_servers": raw_data.get('streaming_servers') or raw_data.get('video_urls', []),
        "download_links": raw_data.get('download_links') or raw_data.get('downloads', []),
        "other_episodes": raw_data.get('other_episodes', []),
        "error": raw_data.get('error', False),
        "message": raw_data.get('message', '')
    }

async def get_detail_episode_data(episode_url):
    """
    Fungsi untuk mendapatkan data detail episode dengan caching.
    """
    logger.info(f"Mengambil detail episode dari API: {episode_url}")
    try:
        get_episode_detail_async = sync_to_async(get_episode_detail)
        raw_result = await get_episode_detail_async(episode_url)
        
        transformed_result = _transform_episode_detail_data(raw_result, episode_url)

        if not transformed_result.get('error'):
            logger.info(f"Berhasil mendapatkan dan mentransformasi data episode: {episode_url}")
            await cache.aset(f"detail_episode_{episode_url.replace('/', '_')}", transformed_result, 60*60*2)
        
        return transformed_result

    except Exception as e:
        logger.error(f"Error saat mengambil detail episode: {e}")
        return _transform_episode_detail_data({}, episode_url)


async def detail_episode_video(request, episode_slug=None):
    """
    View untuk menampilkan detail episode dengan video player.
    """
    response = None
    if not episode_slug:
        logger.warning("Episode slug tidak diberikan")
        context = {'error': 'Episode tidak ditemukan'}
        response = render(request, 'streamapp/detail_episode_video.html', context)
        return response
    
    try:
        logger.info(f"Menerima request untuk episode_slug: {episode_slug}")
        # Gunakan utility function untuk mendapatkan domain yang aktif
        from .utils import get_current_source_domain_async, build_dynamic_url_async
        
        source_domain = await get_current_source_domain_async()
        episode_url = await build_dynamic_url_async(episode_slug)
        logger.info(f"URL episode yang dibangun: {episode_url}")

        episode_data = await get_detail_episode_data(episode_url)

        if not episode_data or episode_data.get('error'):
            logger.warning(f"Data episode tidak ditemukan atau error untuk URL: {episode_url}")
            context = {'error': episode_data.get('message', 'Episode tidak ditemukan') if episode_data else 'Episode tidak ditemukan'}
        else:
            ads = {}
            try:
                positions = [pos[0] for pos in Advertisement.POSITION_CHOICES]
                for position in positions:
                    position_ads = await Advertisement.get_active_ads(position)
                    if position_ads:
                        ads[position] = position_ads[0]
            except Exception as ad_error:
                logger.error(f"Error saat mendapatkan iklan: {ad_error}")

            context = {
                'episode': episode_data,
                'ads': ads
            }

        response = render(request, 'streamapp/detail_episode_video.html', context)

    except Exception as e:
        logger.error(f"Error di view detail_episode_video: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        context = {'error': f'Terjadi kesalahan fatal saat memuat data: {str(e)}'}
        response = render(request, 'streamapp/detail_episode_video.html', context)
    
    return response

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
        raw_search_results = await asyncio.to_thread(search_anime, query)
        
        # Handle struktur data baru dari API
        if isinstance(raw_search_results, dict):
            # Jika hasil memiliki struktur baru dengan confidence_score dan data
            if 'confidence_score' in raw_search_results and 'data' in raw_search_results:
                confidence = raw_search_results.get('confidence_score', 0)
                logger.info(f"Search results dengan confidence score: {confidence}")
                search_results = raw_search_results.get('data', [])
            else:
                # Jika struktur lama, gunakan langsung
                search_results = raw_search_results
        else:
            # Jika bukan dict, anggap sebagai list
            search_results = raw_search_results
        
        # Pastikan search_results adalah list
        if not isinstance(search_results, list):
            logger.warning(f"Search results bukan list: {type(search_results)}")
            search_results = []
        
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
    response = None
    # Ambil parameter query dari query string
    query = request.GET.get('q', '')
    
    # Jika query kosong, kembalikan halaman kosong
    if not query:
        context = {'query': query, 'results': []}
        response = render(request, 'streamapp/search_results.html', context)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
    
    try:
        # Dapatkan hasil pencarian
        search_results = await get_search_results(query)
        
        # Buat context untuk template
        context = {
            'query': query,
            'results': search_results if search_results else [],
            'result_count': len(search_results) if search_results else 0
        }
        
        response = render(request, 'streamapp/search_results.html', context=context)
    
    except Exception as e:
        print(f"Error saat menampilkan hasil pencarian: {e}")
        context = {'query': query, 'error': 'Terjadi kesalahan saat memuat data'}
        response = render(request, 'streamapp/search_results.html', context)

    # Set Cache-Control header to prevent browser caching
    if response:
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

    return response

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


from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .tasks import get_api_status_summary
from streamapp.tasks import check_api_status
from .models import APIEndpoint, APIMonitor
import json

@method_decorator(staff_member_required, name='dispatch')
class APIMonitorDashboardView(TemplateView):
    """
    View untuk menampilkan dashboard monitoring API.
    Hanya dapat diakses oleh staff/admin.
    """
    template_name = 'streamapp/api_monitor_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ambil ringkasan status API
        api_status = get_api_status_summary()
        
        # Ambil informasi tentang API yang sedang digunakan
        current_api_info = get_current_api_info()
        
        # Jika ada current_api.endpoint, ambil objek APIEndpoint yang sebenarnya dari DB
        if current_api_info and current_api_info.get('endpoint') and current_api_info['endpoint'].get('name'):
            try:
                # Ambil objek APIEndpoint yang sebenarnya dari database
                # Gunakan .get() untuk memastikan kita mendapatkan instance model, bukan hanya dict
                current_api_endpoint_obj = APIEndpoint.objects.get(name=current_api_info['endpoint']['name'])
                current_api_info['endpoint'] = current_api_endpoint_obj
            except APIEndpoint.DoesNotExist:
                logger.warning(f"APIEndpoint dengan nama {current_api_info['endpoint']['name']} tidak ditemukan di database.")
                current_api_info['endpoint'] = None # Set to None if not found

        # Tambahkan data ke context
        context['api_status'] = api_status
        context['current_api'] = current_api_info
        context['endpoints'] = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
        context['monitors'] = APIMonitor.objects.all().order_by('-last_checked')[:50]  # Ambil 50 monitor terbaru
        
        # Hitung persentase status
        total_monitors = sum(api_status['status_counts'].values())
        if total_monitors > 0:
            context['status_percentages'] = {
                status: round((count / total_monitors) * 100, 1)
                for status, count in api_status['status_counts'].items()
            }
        else:
            context['status_percentages'] = {status: 0 for status in api_status['status_counts']}
        
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request untuk menjalankan pemeriksaan API secara manual.
        """
        action = request.POST.get('action')
        
        if action == 'check_api':
            try:
                # Jalankan pemeriksaan API
                from streamapp.tasks import check_api_status
                result = check_api_status()
                return HttpResponse(json.dumps({'status': 'success', 'message': 'Pemeriksaan API berhasil dijalankan'}),
                                   content_type='application/json')
            except Exception as e:
                return HttpResponse(json.dumps({'status': 'error', 'message': f'Error: {str(e)}'}),
                                   content_type='application/json', status=500)
        
        return HttpResponse(json.dumps({'status': 'error', 'message': 'Action tidak valid'}),
                           content_type='application/json', status=400)