# Dokumentasi KortekStream

## Deskripsi

KortekStream adalah aplikasi web berbasis Django yang menyediakan layanan streaming anime. Aplikasi ini terdiri dari dua komponen utama:

1. **Frontend Django**: Menampilkan data anime kepada pengguna dengan antarmuka yang responsif dan user-friendly.
2. **Backend API**: Layanan backend berbasis FastAPI yang menyediakan data anime dari berbagai sumber melalui teknik scraping.

## Fitur Utama

- Streaming anime dengan subtitle Indonesia
- Pencarian anime
- Daftar anime terbaru
- Daftar movie anime
- Jadwal rilis anime
- Koleksi pengguna (watchlist, favorites, history)
- **Sistem Fallback API** - Mendukung multiple API dengan failover otomatis
- **Dashboard Monitoring API** - Memantau status dan performa API

## Sistem Fallback API

KortekStream mengimplementasikan sistem fallback API yang memungkinkan aplikasi untuk tetap berfungsi meskipun beberapa API eksternal mengalami gangguan. Sistem ini mendukung multiple API dengan failover otomatis.

### Fitur Utama Fallback API

- **Multiple API Endpoints**: Mendukung beberapa URL API dengan prioritas berbeda
- **Failover Otomatis**: Secara otomatis beralih ke API cadangan jika API utama gagal
- **Prioritas API**: API dengan prioritas lebih tinggi akan dicoba terlebih dahulu
- **Exponential Backoff**: Menghindari mencoba API yang gagal terlalu sering
- **Monitoring Status**: Memantau status dan performa setiap API endpoint

### Komponen Sistem Fallback API

1. **APIEndpoint Model**: Menyimpan URL API dengan prioritas
2. **APIMonitor Model**: Menyimpan status dan metrik API
3. **FallbackAPIClient**: Klien API dengan dukungan fallback
4. **Management Command**: Perintah untuk memeriksa status API secara berkala
5. **Dashboard Monitoring**: Antarmuka untuk memantau status API

### Struktur Folder

```
streamapp/
├── models.py              # Model APIEndpoint dan APIMonitor
├── api_client.py          # Implementasi FallbackAPIClient
├── tasks.py               # Fungsi untuk memeriksa status API
├── management/
│   └── commands/
│       └── check_api_status.py  # Management command untuk memeriksa status API
└── templates/
    └── streamapp/
        └── api_monitor_dashboard.html  # Template dashboard monitoring API
```

## Dashboard Monitoring API

Dashboard Monitoring API menyediakan antarmuka untuk memantau status dan performa API eksternal. Dashboard ini memungkinkan admin untuk:

- Melihat status (up/down/error) dari setiap API endpoint
- Melihat waktu respons (latency) dari setiap API endpoint
- Melihat pesan error jika API mengalami gangguan
- Menjalankan pemeriksaan status API secara manual
- Mengelola API endpoint (menambah, mengedit, menghapus)

### Cara Mengakses Dashboard

Dashboard Monitoring API dapat diakses di `/api-monitor/`. Dashboard ini hanya dapat diakses oleh staff/admin yang sudah login.

### Fitur Dashboard

- **Status Summary**: Ringkasan status semua API endpoint
- **API Endpoints Table**: Tabel yang menampilkan semua API endpoint dengan status
- **Recent Monitors Table**: Tabel yang menampilkan hasil pemeriksaan terbaru
- **Manual Check**: Tombol untuk menjalankan pemeriksaan status API secara manual

## Implementasi Teknis Sistem Fallback API

### Model Database

#### APIEndpoint Model

```python
class APIEndpoint(models.Model):
    """
    Model untuk menyimpan URL API dengan prioritas.
    API dengan prioritas lebih tinggi akan dicoba terlebih dahulu.
    """
    name = models.CharField(max_length=100, verbose_name="Nama API")
    url = models.URLField(max_length=255, verbose_name="URL API")
    priority = models.IntegerField(default=0, verbose_name="Prioritas (semakin tinggi semakin diprioritaskan)")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui pada")
```

#### APIMonitor Model

```python
class APIMonitor(models.Model):
    """
    Model untuk menyimpan status dan metrik API.
    """
    endpoint = models.ForeignKey(APIEndpoint, on_delete=models.CASCADE, related_name="monitors", verbose_name="API Endpoint")
    endpoint_path = models.CharField(max_length=255, verbose_name="Endpoint Path")
    status = models.CharField(max_length=20, verbose_name="Status", default="unknown")
    response_time = models.FloatField(verbose_name="Waktu Respons (ms)", null=True, blank=True)
    last_checked = models.DateTimeField(verbose_name="Terakhir Diperiksa", auto_now=True)
    error_message = models.TextField(verbose_name="Pesan Error", null=True, blank=True)
    response_data = models.TextField(verbose_name="Data Respons", null=True, blank=True)
```

### FallbackAPIClient

FallbackAPIClient adalah kelas yang menangani komunikasi dengan API eksternal dengan dukungan fallback. Kelas ini akan mencoba setiap API endpoint secara berurutan berdasarkan prioritas. Jika API endpoint gagal, kelas ini akan mencoba API endpoint berikutnya.

```python
class FallbackAPIClient:
    """
    Client for interacting with multiple FastAPI backends with fallback support.
    """
    def __init__(self):
        self.endpoints = get_api_endpoints()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "KortekStream Django Client",
            "Accept": "application/json",
        })
        # Cache for failed endpoints to avoid retrying too often
        self.failed_endpoints = {}
        # Default timeout values
        self.connect_timeout = 3  # seconds
        self.read_timeout = 10    # seconds
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make GET request to API with fallback support.
        """
        # Try each endpoint in order of priority
        for api_endpoint in self.endpoints:
            # Skip endpoints that have failed recently
            if not self._should_retry_endpoint(api_endpoint.url):
                continue
            
            try:
                # Try to get response from this endpoint
                result = self._make_request(api_endpoint, endpoint, params)
                return result
            except Exception as e:
                # If this endpoint fails, try the next one
                continue
        
        # If we get here, all endpoints failed
        raise Exception("All API endpoints failed")
```

### Pemeriksaan Status API

Pemeriksaan status API dilakukan oleh fungsi `check_api_status()` di `tasks.py`. Fungsi ini akan memeriksa status setiap endpoint API untuk beberapa endpoint path umum.

```python
def check_api_status():
    """
    Memeriksa status semua API endpoint yang aktif.
    """
    # Ambil semua endpoint API yang aktif
    endpoints = APIEndpoint.objects.filter(is_active=True).order_by('-priority')
    
    # Periksa setiap endpoint
    for endpoint in endpoints:
        # Periksa setiap path
        for path in ENDPOINTS_TO_CHECK:
            # Gunakan metode check_endpoint dari model APIMonitor
            monitor = APIMonitor.check_endpoint(endpoint, path)
```

## Pengujian Sistem Fallback API

Untuk menguji sistem fallback API, kita telah membuat script pengujian di `tests/test_api_fallback.py`. Script ini akan menjalankan server FastAPI dummy di beberapa port dan mensimulasikan API yang down.

### Cara Menjalankan Pengujian

```bash
python tests/test_api_fallback.py
```

### Skenario Pengujian

1. **Semua Server Aktif**: Memastikan API client menggunakan server dengan prioritas tertinggi.
2. **Server Prioritas Tertinggi Down**: Memastikan API client fallback ke server dengan prioritas kedua.
3. **Server Prioritas Kedua Down**: Memastikan API client fallback ke server dengan prioritas ketiga.
4. **Semua Server Down**: Memastikan API client menangani kasus ketika semua server down.
5. **Pemulihan Server**: Memastikan API client kembali menggunakan server dengan prioritas tertinggi ketika server tersebut kembali aktif.
6. **Pemeriksaan Status API**: Memastikan pemeriksaan status API berfungsi dengan benar.

## Struktur API Backend

### Struktur Folder

```
fastapi_app/app/api/
├── __init__.py            # Inisialisasi package api
├── api.py                 # Konfigurasi router utama
└── endpoints/             # Implementasi endpoint API
    ├── __init__.py        # Inisialisasi package endpoints
    ├── anime_detail.py    # Endpoint untuk detail anime
    ├── anime_terbaru.py   # Endpoint untuk anime terbaru
    ├── episode_detail.py  # Endpoint untuk detail episode
    ├── home.py            # Endpoint untuk halaman utama
    ├── jadwal_rilis.py    # Endpoint untuk jadwal rilis
    ├── movie.py           # Endpoint untuk daftar movie
    └── search.py          # Endpoint untuk pencarian
```

### Komponen Utama Backend API

1. **api.py**: Mendefinisikan router utama dan mengimpor semua endpoint.
2. **endpoints/**: Berisi implementasi untuk setiap endpoint API.

## Endpoint API

API ini menyediakan beberapa endpoint utama:

| Endpoint | Metode | Deskripsi | Parameter |
|----------|--------|-----------|-----------|
| `/api/v1/home/` | GET | Mendapatkan data halaman utama | - |
| `/api/v1/jadwal-rilis/` | GET | Mendapatkan jadwal rilis untuk semua hari | - |
| `/api/v1/jadwal-rilis/{day}` | GET | Mendapatkan jadwal rilis untuk hari tertentu | `day`: Hari dalam bahasa Inggris (monday, tuesday, dll.) |
| `/api/v1/anime-terbaru/` | GET | Mendapatkan daftar anime terbaru | `page`: Nomor halaman (default: 1) |
| `/api/v1/movie/` | GET | Mendapatkan daftar movie anime | `page`: Nomor halaman (default: 1) |
| `/api/v1/anime-detail/` | GET | Mendapatkan detail anime | `anime_slug`: Slug anime |
| `/api/v1/episode-detail/` | GET | Mendapatkan detail episode | `episode_url`: URL episode |
| `/api/v1/search/` | GET | Mencari anime | `query`: Kata kunci pencarian |

## Skema Data

API ini menggunakan beberapa model data utama:

### AnimeBase

Model dasar untuk data anime:

```python
class AnimeBase(BaseModel):
    judul: str
    url_anime: str
    anime_slug: Optional[str] = None
    status: Optional[str] = None
    tipe: Optional[str] = None
    skor: Optional[str] = None
    penonton: Optional[str] = None
    sinopsis: Optional[str] = None
    genre: Optional[List[str]] = None
    url_cover: Optional[str] = None
```

### AnimeDetail

Model untuk detail anime:

```python
class AnimeDetail(AnimeBase):
    details: Optional[Dict[str, Any]] = None
    rating: Optional[Dict[str, Any]] = None
    episode_list: Optional[List[AnimeEpisode]] = None
    recommendations: Optional[List[Any]] = None
```

### EpisodeDetail

Model untuk detail episode:

```python
class EpisodeDetail(BaseModel):
    title: str
    release_info: Optional[str] = None
    streaming_servers: List[EpisodeServer] = []
    download_links: Dict[str, Dict[str, List[DownloadProvider]]] = {}
    navigation: EpisodeNavigation = Field(default_factory=EpisodeNavigation)
    anime_info: Dict[str, Any] = {}
    other_episodes: List[Dict[str, Any]] = []
```

### AnimeTerbaru

Model untuk anime terbaru:

```python
class AnimeTerbaru(BaseModel):
    judul: str
    url: str
    anime_slug: Optional[str] = None
    episode: Optional[str] = None
    rilis: Optional[str] = None
    cover: Optional[str] = None
```

### AnimeMovie

Model untuk movie anime:

```python
class AnimeMovie(BaseModel):
    judul: str
    url: str
    anime_slug: Optional[str] = None
    tanggal: Optional[str] = None
    cover: Optional[str] = None
    genres: Optional[List[str]] = None
```

### AnimeSchedule

Model untuk jadwal rilis anime:

```python
class AnimeSchedule(BaseModel):
    Monday: List[AnimeScheduleItem] = []
    Tuesday: List[AnimeScheduleItem] = []
    Wednesday: List[AnimeScheduleItem] = []
    Thursday: List[AnimeScheduleItem] = []
    Friday: List[AnimeScheduleItem] = []
    Saturday: List[AnimeScheduleItem] = []
    Sunday: List[AnimeScheduleItem] = []
```

### HomeData

Model untuk data halaman utama:

```python
class HomeData(BaseModel):
    top10: List[AnimeMingguan] = []
    new_eps: List[AnimeTerbaru] = []
    movies: List[AnimeMovie] = []
    jadwal_rilis: Optional[AnimeSchedule] = None
```

## Konfigurasi dan Cache

### Konfigurasi

Konfigurasi API diatur dalam file `core/config.py`:

```python
class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "KortekStream API"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Anime Source Configuration
    ANIME_SOURCES: Dict[str, Dict[str, Any]] = {
        "samehadaku": {
            "base_url": os.getenv("SAMEHADAKU_BASE_URL", "https://v1.samehadaku.how"),
            "search_url": os.getenv("SAMEHADAKU_SEARCH_URL", "https://samehadaku.now"),
            "api_url": os.getenv("SAMEHADAKU_API_URL", "https://samehadaku.now/wp-json/custom/v1"),
            "active": True,
        },
    }

    # Cache Configuration
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", 600))  # 10 menit
    CACHE_LONG_TTL: int = int(os.getenv("CACHE_LONG_TTL", 3600))  # 1 jam
    CACHE_VERY_LONG_TTL: int = int(os.getenv("CACHE_VERY_LONG_TTL", 86400))  # 24 jam
```

### Cache

API menggunakan sistem cache sederhana berbasis memori untuk meningkatkan performa:

```python
def get_from_cache_or_fetch(
    key: str, 
    fetch_func: Callable[..., T], 
    *args, 
    ttl: Optional[int] = None, 
    **kwargs
) -> T:
    """
    Get data from cache or fetch it using the provided function.
    """
    current_time = time.time()
    cache_ttl = ttl if ttl is not None else settings.CACHE_TTL
    
    if key in cache and (current_time - cache[key]["timestamp"]) < cache_ttl:
        print(f"CACHE HIT: Mengambil data dari cache untuk key: {key}")
        return cache[key]["data"]
    
    print(f"CACHE MISS: Melakukan fetch baru untuk key: {key}")
    try:
        data = fetch_func(*args, **kwargs)
        if data is not None:
            cache[key] = {"timestamp": current_time, "data": data}
        return data
    except Exception as e:
        print(f"Error saat fetching {key}: {e}")
        raise
```

## Scraper

API menggunakan sistem scraper untuk mengambil data dari situs anime. Saat ini hanya mendukung Samehadaku, tetapi dirancang untuk dapat menambahkan sumber lain di masa depan.

### ScraperFactory

Factory class untuk membuat instance scraper:

```python
class ScraperFactory:
    _scrapers: Dict[str, BaseScraper] = {}
    _scraper_classes: Dict[str, Type[BaseScraper]] = {
        "samehadaku": SamehadakuScraper,
        # Tambahkan scraper lain di sini
    }
    
    @classmethod
    def get_default_scraper(cls) -> Optional[BaseScraper]:
        """
        Get default scraper (first active scraper).
        """
        active_scrapers = cls.get_active_scrapers()
        return active_scrapers[0] if active_scrapers else None
```

## Implementasi Penanganan Perbedaan Data Antar API

Salah satu tantangan utama dalam sistem fallback API adalah menangani perbedaan format data, terutama judul anime dan slug, dari berbagai sumber web scraping. Berikut adalah penjelasan tentang bagaimana KortekStream menangani perbedaan ini:

### Penanganan Perbedaan Judul Anime

Judul anime dapat bervariasi antar sumber web scraping. Misalnya, satu sumber mungkin menggunakan judul Jepang asli, sementara yang lain menggunakan judul terjemahan bahasa Inggris atau Indonesia. Untuk menangani ini:

1. **Normalisasi Judul**: Sistem melakukan normalisasi judul dengan menghapus karakter khusus dan mengubah ke lowercase.
2. **Fuzzy Matching**: Menggunakan algoritma fuzzy matching untuk mencocokkan judul yang mirip tapi tidak identik.
3. **Mapping Database**: Menyimpan mapping judul dari berbagai sumber ke judul standar yang digunakan di frontend.

### Penanganan Perbedaan Slug Anime

Slug anime digunakan untuk URL dan identifikasi unik anime. Perbedaan slug antar sumber dapat menyebabkan masalah navigasi dan linking:

1. **Ekstraksi Slug**: Sistem mengekstrak slug dari URL anime jika tidak tersedia secara eksplisit.
2. **Validasi Slug**: Sebelum menggunakan slug untuk navigasi, sistem memvalidasi keberadaan dan format slug.
3. **Fallback ke ID**: Jika slug tidak tersedia atau tidak valid, sistem dapat menggunakan ID numerik sebagai alternatif.
4. **Conditional Rendering**: Template menggunakan pengecekan kondisional untuk menangani kasus di mana slug tidak tersedia.

### Contoh Implementasi di Template

```html
{% if anime.anime_slug %}
    <a href="{% url 'detail_anime' anime_slug=anime.anime_slug %}">{{ anime.judul }}</a>
{% elif anime.url_anime %}
    {% with anime_slug=anime.url_anime|extract_slug %}
        {% if anime_slug %}
            <a href="{% url 'detail_anime' anime_slug=anime_slug %}">{{ anime.judul }}</a>
        {% else %}
            <span>{{ anime.judul }}</span>
        {% endif %}
    {% endwith %}
{% else %}
    <span>{{ anime.judul }}</span>
{% endif %}
```

### Contoh Implementasi di View

```python
def extract_slug_from_url(url):
    """Ekstrak slug dari URL anime."""
    if not url:
        return None
    
    # Pola URL: https://example.com/anime/one-piece/
    match = re.search(r'/anime/([^/]+)/?', url)
    if match:
        return match.group(1)
    
    return None

def detail_anime(request, anime_slug=None):
    """View untuk detail anime dengan penanganan slug."""
    if not anime_slug:
        # Redirect ke halaman utama jika slug tidak ada
        return redirect('index')
    
    try:
        # Coba dapatkan detail anime dengan slug
        anime_detail = api_client.get(f"anime-detail/?anime_slug={anime_slug}")
        return render(request, 'streamapp/detail_anime.html', {'anime': anime_detail})
    except Exception as e:
        # Tangani error jika API gagal
        messages.error(request, f"Gagal mendapatkan detail anime: {str(e)}")
        return redirect('index')
```

### Contoh Implementasi di API Client

```python
def get_current_api_info(self):
    """
    Mendapatkan informasi tentang API yang sedang digunakan.
    """
    if hasattr(self, 'current_api') and self.current_api:
        endpoint = APIEndpoint.objects.filter(url=self.current_api).first()
        if endpoint:
            return {
                'name': endpoint.name,
                'url': endpoint.url,
                'priority': endpoint.priority,
                'is_active': endpoint.is_active
            }
    return None

def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Make GET request to API with fallback support.
    """
    # Refresh endpoints list to ensure we have the latest status
    self.refresh_endpoints()
    
    # Try each endpoint in order of priority
    for api_endpoint in self.endpoints:
        # Skip endpoints that have failed recently
        if not self._should_retry_endpoint(api_endpoint.url):
            continue
        
        try:
            # Try to get response from this endpoint
            result = self._make_request(api_endpoint, endpoint, params)
            # Store the current API being used
            self.current_api = api_endpoint.url
            return result
        except Exception as e:
            # If this endpoint fails, try the next one
            continue
    
    # If we get here, all endpoints failed
    raise Exception("All API endpoints failed")
```

## Struktur API Fallback yang Direkomendasikan

Untuk mengembangkan API fallback yang efektif, berikut adalah struktur yang direkomendasikan:

### 1. Struktur Endpoint API

Setiap API endpoint harus mengikuti struktur yang konsisten:

```
/api/v1/
├── home/                  # Data halaman utama
├── anime-terbaru/         # Daftar anime terbaru
├── movie/                 # Daftar movie anime
├── jadwal-rilis/          # Jadwal rilis anime
├── anime-detail/          # Detail anime (parameter: anime_slug)
├── episode-detail/        # Detail episode (parameter: episode_url)
└── search/                # Pencarian anime (parameter: query)
```

### 2. Struktur Response JSON

Setiap endpoint harus mengembalikan response JSON dengan struktur yang konsisten:

```json
{
  "status": "success",
  "message": "Data berhasil diambil",
  "data": {
    // Data spesifik untuk endpoint
  },
  "meta": {
    "source": "nama_sumber",
    "timestamp": "2025-07-31T12:00:00Z",
    "version": "1.0"
  }
}
```

### 3. Penanganan Error

Response error harus mengikuti format yang konsisten:

```json
{
  "status": "error",
  "message": "Pesan error yang informatif",
  "error_code": "ERROR_CODE",
  "meta": {
    "source": "nama_sumber",
    "timestamp": "2025-07-31T12:00:00Z"
  }
}
```

## Hal-hal yang Perlu Diperhatikan dalam Pengembangan API Fallback

### 1. Konsistensi Format Data

Pastikan semua API endpoint mengembalikan data dengan format yang konsisten, terutama untuk:

- **Judul Anime**: Gunakan format yang konsisten (misalnya judul Jepang dengan terjemahan dalam kurung).
- **Slug**: Pastikan slug selalu tersedia dan valid untuk navigasi.
- **URL**: Gunakan format URL yang konsisten untuk gambar, episode, dll.
- **Metadata**: Sertakan metadata yang konsisten seperti genre, status, skor, dll.

### 2. Penanganan Error yang Robust

- Implementasikan penanganan error yang robust di semua level (API, client, template).
- Gunakan timeout yang sesuai untuk mencegah permintaan yang terlalu lama.
- Implementasikan retry mechanism dengan exponential backoff.
- Log semua error untuk analisis dan debugging.

### 3. Caching yang Efektif

- Cache hasil API untuk mengurangi beban server dan meningkatkan performa.
- Gunakan TTL (Time To Live) yang sesuai untuk berbagai jenis data.
- Implementasikan invalidasi cache yang cerdas ketika data berubah.

### 4. Monitoring dan Alerting

- Monitor status dan performa semua API endpoint.
- Implementasikan alerting untuk notifikasi ketika API endpoint down.
- Kumpulkan metrik seperti response time, error rate, dll.

## Cara Menggunakan Sistem Fallback API

### Menambahkan API Endpoint

1. Buka admin panel Django di `/admin/`
2. Navigasi ke "API Endpoints" di bagian "Streamapp"
3. Klik "Add API Endpoint" untuk menambahkan API endpoint baru
4. Isi form dengan informasi berikut:
   - **Name**: Nama API endpoint (misalnya "API Utama", "API Cadangan 1")
   - **URL**: URL API endpoint (misalnya "https://api1.example.com/api/v1")
   - **Priority**: Prioritas API endpoint (semakin tinggi semakin diprioritaskan)
   - **Is Active**: Centang jika API endpoint aktif
5. Klik "Save" untuk menyimpan API endpoint

### Menjalankan Pemeriksaan Status API

#### Melalui Management Command

Anda dapat menjalankan pemeriksaan status API secara manual menggunakan management command:

```bash
python manage.py check_api_status
```

Untuk menampilkan output yang lebih detail, tambahkan flag `--verbose`:

```bash
python manage.py check_api_status --verbose
```

#### Melalui Dashboard

1. Buka dashboard monitoring API di `/api-monitor/`
2. Klik tombol "Periksa Status API" untuk menjalankan pemeriksaan status API secara manual

### Mengatur Pemeriksaan Status API Berkala

Anda dapat mengatur pemeriksaan status API berkala menggunakan cron job atau task scheduler lainnya.

#### Contoh Cron Job

Untuk menjalankan pemeriksaan status API setiap 15 menit:

```
*/15 * * * * cd /path/to/project && python manage.py check_api_status
```

## Cara Menjalankan Aplikasi

1. Pastikan semua dependensi terinstal:
   ```
   pip install -r requirements.txt
   ```

2. Jalankan migrasi database:
   ```
   python manage.py migrate
   ```

3. Tambahkan API endpoint di admin panel atau melalui shell:
   ```
   python manage.py shell -c "from streamapp.models import APIEndpoint; APIEndpoint.objects.create(name='API Utama', url='http://localhost:8001/api/v1', priority=100, is_active=True)"
   ```

4. Jalankan server Django:
   ```
   python manage.py runserver
   ```

5. Aplikasi akan berjalan di `http://localhost:8000`

6. Untuk menjalankan API backend:
   ```
   cd fastapi_app
   python run.py
   ```

7. API backend akan berjalan di `http://localhost:8001`

8. Dokumentasi API tersedia di `http://localhost:8001/docs`

## Contoh Penggunaan API dan Struktur JSON Lengkap

Berikut adalah contoh penggunaan API dan struktur JSON lengkap untuk setiap endpoint. Semua endpoint mengembalikan response dengan format yang konsisten, termasuk status, message, data, dan meta.

### 1. Mendapatkan Data Halaman Utama

```bash
curl -X GET "http://localhost:8001/api/v1/home/"
```

#### Contoh Respons JSON:

```json
{
  "status": "success",
  "message": "Data berhasil diambil",
  "data": {
    "top10": [
      {
        "judul": "One Piece",
        "url": "https://v1.samehadaku.how/anime/one-piece/",
        "anime_slug": "one-piece",
        "rating": "8.73",
        "cover": "https://v1.samehadaku.how/wp-content/uploads/2020/04/E5RxYkWX0AAwdGH.png.jpg",
        "genres": ["Action", "Adventure", "Fantasy"]
      },
      // ... lebih banyak anime
    ],
    "new_eps": [
      {
        "judul": "Dr. Stone Season 4 Part 2",
        "url": "https://v1.samehadaku.how/anime/dr-stone-season-4-part-2/",
        "anime_slug": "dr-stone-season-4-part-2",
        "episode": "4",
        "rilis": "3 hours yang lalu",
        "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Dr.-Stone-Season-4-Part-2-Episode-4-1.jpg"
      },
      // ... lebih banyak episode
    ],
    "movies": [
      {
        "judul": "Sidonia no Kishi Ai Tsumugu Hoshi",
        "url": "https://v1.samehadaku.how/anime/sidonia-no-kishi-ai-tsumugu-hoshi/",
        "anime_slug": "sidonia-no-kishi-ai-tsumugu-hoshi",
        "tanggal": "Jun 4, 2021",
        "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/07/108354.jpg",
        "genres": ["Action", "Sci-Fi"]
      },
      // ... lebih banyak movie
    ],
    "jadwal_rilis": {
      "Monday": [
        {
          "title": "Busamen Gachi Fighter",
          "url": "https://v1.samehadaku.how/anime/busamen-gachi-fighter/",
          "anime_slug": "busamen-gachi-fighter",
          "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/150515.jpg",
          "type": "TV",
          "score": "6.68",
          "genres": ["Action", "Adventure"],
          "release_time": "00:00"
        }
      ],
      // ... jadwal untuk hari lain
    }
  },
  "meta": {
    "source": "samehadaku",
    "timestamp": "2025-07-31T12:00:00Z",
    "version": "1.0"
  }
}
```

### 2. Mendapatkan Detail Anime

```bash
curl -X GET "http://localhost:8001/api/v1/anime-detail/?anime_slug=one-piece"
```

#### Contoh Respons JSON:

```json
{
  "status": "success",
  "message": "Data berhasil diambil",
  "data": {
    "judul": "One Piece",
    "url_anime": "https://v1.samehadaku.how/anime/one-piece/",
    "anime_slug": "one-piece",
    "status": "Ongoing",
    "tipe": "TV",
    "skor": "8.73",
    "penonton": "1,234,567",
    "sinopsis": "Gol D. Roger dikenal sebagai Raja Bajak Laut, orang terkuat dan paling terkenal yang pernah mengarungi Grand Line...",
    "genre": ["Action", "Adventure", "Comedy", "Fantasy", "Shounen", "Super Power"],
    "url_cover": "https://v1.samehadaku.how/wp-content/uploads/2020/04/E5RxYkWX0AAwdGH.png.jpg",
    "details": {
      "Japanese": "ワンピース",
      "Synonyms": "OP",
      "Aired": "Oct 20, 1999 to ?",
      "Premiered": "Fall 1999",
      "Duration": "24 min. per ep.",
      "Studios": ["Toei Animation"],
      "Producers": ["Fuji TV", "TAP", "Shueisha"]
    },
    "rating": {
      "value": "8.73",
      "votes": "123,456"
    },
    "episode_list": [
      {
        "episode": "1080",
        "title": "Luffy's Determination! The Straw Hat Promise!",
        "date": "Jul 28, 2025",
        "url": "https://v1.samehadaku.how/one-piece-episode-1080/",
        "slug": "one-piece-episode-1080"
      },
      // ... lebih banyak episode
    ],
    "recommendations": [
      {
        "judul": "Naruto Shippuden",
        "url": "https://v1.samehadaku.how/anime/naruto-shippuden/",
        "anime_slug": "naruto-shippuden",
        "cover": "https://v1.samehadaku.how/wp-content/uploads/2020/04/naruto-shippuden.jpg"
      },
      // ... lebih banyak rekomendasi
    ]
  },
  "meta": {
    "source": "samehadaku",
    "timestamp": "2025-07-31T12:00:00Z",
    "version": "1.0"
  }
}
```

### 3. Mendapatkan Detail Episode

```bash
curl -X GET "http://localhost:8001/api/v1/episode-detail/?episode_url=https://v1.samehadaku.how/one-piece-episode-1080/"
```

#### Contoh Respons JSON:

```json
{
  "status": "success",
  "message": "Data berhasil diambil",
  "data": {
    "title": "One Piece Episode 1080 Subtitle Indonesia",
    "release_info": "Released on Jul 28, 2025",
    "streaming_servers": [
      {
        "name": "Server 1",
        "url": "https://example.com/embed/abc123"
      },
      {
        "name": "Server 2",
        "url": "https://example2.com/embed/def456"
      }
    ],
    "download_links": {
      "MP4": {
        "360p": [
          {
            "provider": "GDrive",
            "url": "https://drive.google.com/file/d/abc123/view"
          },
          {
            "provider": "Zippyshare",
            "url": "https://www10.zippyshare.com/v/abc123/file.html"
          }
        ],
        "480p": [
          {
            "provider": "GDrive",
            "url": "https://drive.google.com/file/d/def456/view"
          },
          {
            "provider": "Zippyshare",
            "url": "https://www10.zippyshare.com/v/def456/file.html"
          }
        ],
        "720p": [
          {
            "provider": "GDrive",
            "url": "https://drive.google.com/file/d/ghi789/view"
          },
          {
            "provider": "Zippyshare",
            "url": "https://www10.zippyshare.com/v/ghi789/file.html"
          }
        ]
      },
      "MKV": {
        "720p": [
          {
            "provider": "GDrive",
            "url": "https://drive.google.com/file/d/jkl012/view"
          },
          {
            "provider": "Zippyshare",
            "url": "https://www10.zippyshare.com/v/jkl012/file.html"
          }
        ],
        "1080p": [
          {
            "provider": "GDrive",
            "url": "https://drive.google.com/file/d/mno345/view"
          },
          {
            "provider": "Zippyshare",
            "url": "https://www10.zippyshare.com/v/mno345/file.html"
          }
        ]
      }
    },
    "navigation": {
      "prev_episode": {
        "url": "https://v1.samehadaku.how/one-piece-episode-1079/",
        "episode": "1079"
      },
      "next_episode": null
    },
    "anime_info": {
      "title": "One Piece",
      "url": "https://v1.samehadaku.how/anime/one-piece/",
      "anime_slug": "one-piece"
    },
    "other_episodes": [
      {
        "episode": "1079",
        "url": "https://v1.samehadaku.how/one-piece-episode-1079/"
      },
      {
        "episode": "1078",
        "url": "https://v1.samehadaku.how/one-piece-episode-1078/"
      },
      // ... lebih banyak episode
    ]
  },
  "meta": {
    "source": "samehadaku",
    "timestamp": "2025-07-31T12:00:00Z",
    "version": "1.0"
  }
}
```

### 4. Mencari Anime

```bash
curl -X GET "http://localhost:8001/api/v1/search/?query=naruto"
```

#### Contoh Respons JSON:

```json
{
  "status": "success",
  "message": "Data berhasil diambil",
  "data": {
    "results": [
      {
        "judul": "Naruto",
        "url": "https://v1.samehadaku.how/anime/naruto/",
        "anime_slug": "naruto",
        "cover": "https://v1.samehadaku.how/wp-content/uploads/2020/04/naruto.jpg",
        "status": "Completed",
        "tipe": "TV",
        "skor": "8.15",
        "genres": ["Action", "Adventure", "Comedy", "Martial Arts", "Shounen", "Super Power"]
      },
      {
        "judul": "Naruto Shippuden",
        "url": "https://v1.samehadaku.how/anime/naruto-shippuden/",
        "anime_slug": "naruto-shippuden",
        "cover": "https://v1.samehadaku.how/wp-content/uploads/2020/04/naruto-shippuden.jpg",
        "status": "Completed",
        "tipe": "TV",
        "skor": "8.57",
        "genres": ["Action", "Adventure", "Comedy", "Martial Arts", "Shounen", "Super Power"]
      },
      // ... lebih banyak hasil
    ],
    "total": 10,
    "page": 1,
    "total_pages": 1
  },
  "meta": {
    "source": "samehadaku",
    "timestamp": "2025-07-31T12:00:00Z",
    "version": "1.0",
    "query": "naruto"
  }
}
```

### 5. Mendapatkan Anime Terbaru

```bash
curl -X GET "http://localhost:8001/api/v1/anime-terbaru/?page=1"
```

#### Contoh Respons JSON:

```json
{
  "status": "success",
  "message": "Data berhasil diambil",
  "data": {
    "results": [
      {
        "judul": "Dr. Stone Season 4 Part 2",
        "url": "https://v1.samehadaku.how/dr-stone-season-4-part-2-episode-4/",
        "anime_slug": "dr-stone-season-4-part-2",
        "episode": "4",
        "rilis": "3 hours yang lalu",
        "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Dr.-Stone-Season-4-Part-2-Episode-4-1.jpg"
      },
      {
        "judul": "One Piece",
        "url": "https://v1.samehadaku.how/one-piece-episode-1080/",
        "anime_slug": "one-piece",
        "episode": "1080",
        "rilis": "3 days yang lalu",
        "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/07/One-Piece-Episode-1080.jpg"
      },
      // ... lebih banyak anime
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 50,
      "has_next_page": true,
      "has_prev_page": false
    }
  },
  "meta": {
    "source": "samehadaku",
    "timestamp": "2025-07-31T12:00:00Z",
    "version": "1.0"
  }
}
```

## Implementasi Backend untuk API Fallback

Berikut adalah panduan implementasi backend untuk sistem API fallback:

### 1. Struktur Kode Backend

```
fastapi_app/
├── app/
│   ├── __init__.py
│   ├── main.py                # Entry point aplikasi
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Konfigurasi aplikasi
│   │   └── cache.py           # Implementasi cache
│   ├── api/
│   │   ├── __init__.py
│   │   ├── api.py             # Router utama
│   │   └── endpoints/         # Implementasi endpoint
│   │       ├── __init__.py
│   │       ├── home.py
│   │       ├── anime_detail.py
│   │       └── ...
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py            # Scraper base class
│   │   ├── samehadaku.py      # Implementasi scraper Samehadaku
│   │   └── ...                # Scraper lainnya
│   └── utils/
│       ├── __init__.py
│       └── helpers.py         # Fungsi helper
└── run.py                     # Script untuk menjalankan aplikasi
```

### 2. Implementasi Scraper Base Class

```python
# app/scrapers/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BaseScraper(ABC):
    """
    Base class untuk semua scraper.
    """
    def __init__(self, base_url: str, search_url: str = None, api_url: str = None):
        self.base_url = base_url
        self.search_url = search_url or base_url
        self.api_url = api_url
    
    @abstractmethod
    def get_home_data(self) -> Dict[str, Any]:
        """
        Mendapatkan data untuk halaman utama.
        """
        pass
    
    @abstractmethod
    def get_anime_detail(self, anime_slug: str) -> Dict[str, Any]:
        """
        Mendapatkan detail anime berdasarkan slug.
        """
        pass
    
    @abstractmethod
    def get_episode_detail(self, episode_url: str) -> Dict[str, Any]:
        """
        Mendapatkan detail episode berdasarkan URL.
        """
        pass
    
    @abstractmethod
    def search_anime(self, query: str, page: int = 1) -> Dict[str, Any]:
        """
        Mencari anime berdasarkan query.
        """
        pass
    
    @abstractmethod
    def get_anime_terbaru(self, page: int = 1) -> Dict[str, Any]:
        """
        Mendapatkan daftar anime terbaru.
        """
        pass
    
    @abstractmethod
    def get_anime_movie(self, page: int = 1) -> Dict[str, Any]:
        """
        Mendapatkan daftar movie anime.
        """
        pass
    
    @abstractmethod
    def get_jadwal_rilis(self, day: Optional[str] = None) -> Dict[str, Any]:
        """
        Mendapatkan jadwal rilis anime.
        """
        pass
    
    def extract_slug_from_url(self, url: str) -> Optional[str]:
        """
        Ekstrak slug dari URL anime.
        """
        if not url:
            return None
        
        # Pola URL: https://example.com/anime/one-piece/
        import re
        match = re.search(r'/anime/([^/]+)/?', url)
        if match:
            return match.group(1)
        
        return None
    
    def normalize_title(self, title: str) -> str:
        """
        Normalisasi judul anime.
        """
        if not title:
            return ""
        
        # Hapus karakter khusus dan ubah ke lowercase
        import re
        normalized = re.sub(r'[^\w\s]', '', title).lower()
        return normalized
```

### 3. Implementasi Scraper Factory

```python
# app/scrapers/__init__.py
from typing import Dict, List, Type, Optional
from app.core.config import settings
from app.scrapers.base import BaseScraper
from app.scrapers.samehadaku import SamehadakuScraper
# Import scraper lainnya di sini

class ScraperFactory:
    """
    Factory class untuk membuat instance scraper.
    """
    _scrapers: Dict[str, BaseScraper] = {}
    _scraper_classes: Dict[str, Type[BaseScraper]] = {
        "samehadaku": SamehadakuScraper,
        # Tambahkan scraper lain di sini
    }
    
    @classmethod
    def get_scraper(cls, name: str) -> Optional[BaseScraper]:
        """
        Get scraper by name.
        """
        if name in cls._scrapers:
            return cls._scrapers[name]
        
        if name not in cls._scraper_classes or name not in settings.ANIME_SOURCES:
            return None
        
        source_config = settings.ANIME_SOURCES[name]
        if not source_config.get("active", False):
            return None
        
        scraper_class = cls._scraper_classes[name]
        scraper = scraper_class(
            base_url=source_config["base_url"],
            search_url=source_config.get("search_url"),
            api_url=source_config.get("api_url")
        )
        cls._scrapers[name] = scraper
        return scraper
    
    @classmethod
    def get_default_scraper(cls) -> Optional[BaseScraper]:
        """
        Get default scraper (first active scraper).
        """
        active_scrapers = cls.get_active_scrapers()
        return active_scrapers[0] if active_scrapers else None
    
    @classmethod
    def get_active_scrapers(cls) -> List[BaseScraper]:
        """
        Get all active scrapers.
        """
        active_scrapers = []
        for name, config in settings.ANIME_SOURCES.items():
            if config.get("active", False):
                scraper = cls.get_scraper(name)
                if scraper:
                    active_scrapers.append(scraper)
        return active_scrapers
```

### 4. Implementasi Endpoint dengan Fallback

```python
# app/api/endpoints/anime_detail.py
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.core.cache import get_from_cache_or_fetch
from app.models.schemas import AnimeDetail, ErrorResponse
from app.scrapers import ScraperFactory

router = APIRouter()

@router.get(
    "/anime-detail/",
    response_model=AnimeDetail,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_anime_detail(anime_slug: str = Query(..., description="Slug anime")):
    """
    Mendapatkan detail anime berdasarkan slug.
    """
    cache_key = f"anime_detail:{anime_slug}"
    
    # Fungsi untuk mencoba semua scraper
    def fetch_with_fallback():
        # Coba semua scraper aktif
        scrapers = ScraperFactory.get_active_scrapers()
        last_error = None
        
        for scraper in scrapers:
            try:
                result = scraper.get_anime_detail(anime_slug)
                # Tambahkan informasi sumber
                result["meta"] = {
                    "source": scraper.__class__.__name__.replace("Scraper", "").lower(),
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0"
                }
                return result
            except Exception as e:
                last_error = e
                continue
        
        # Jika semua scraper gagal
        if last_error:
            raise HTTPException(status_code=500, detail=f"Semua scraper gagal: {str(last_error)}")
        else:
            raise HTTPException(status_code=404, detail=f"Anime dengan slug '{anime_slug}' tidak ditemukan")
    
    # Coba ambil dari cache atau fetch baru
    try:
        return get_from_cache_or_fetch(cache_key, fetch_with_fallback)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
```

### 5. Implementasi Health Check Endpoint

```python
# app/api/endpoints/health.py
from fastapi import APIRouter, HTTPException
from app.scrapers import ScraperFactory
from typing import Dict, Any
import time

router = APIRouter()

@router.get("/health/")
async def health_check() -> Dict[str, Any]:
    """
    Endpoint untuk health check semua scraper.
    """
    results = {}
    scrapers = ScraperFactory.get_active_scrapers()
    
    for scraper in scrapers:
        scraper_name = scraper.__class__.__name__.replace("Scraper", "").lower()
        start_time = time.time()
        try:
            # Coba ambil data sederhana untuk mengecek health
            scraper.get_jadwal_rilis()
            end_time = time.time()
            results[scraper_name] = {
                "status": "up",
                "response_time": round((end_time - start_time) * 1000, 2),  # ms
                "timestamp": time.time()
            }
        except Exception as e:
            end_time = time.time()
            results[scraper_name] = {
                "status": "down",
                "error": str(e),
                "response_time": round((end_time - start_time) * 1000, 2),  # ms
                "timestamp": time.time()
            }
    
    return {
        "status": "success",
        "message": "Health check completed",
        "data": results
    }
```

Dengan implementasi di atas, sistem API fallback akan mencoba semua scraper aktif secara berurutan jika salah satu gagal. Ini memastikan bahwa aplikasi tetap berfungsi meskipun beberapa sumber data mengalami gangguan.