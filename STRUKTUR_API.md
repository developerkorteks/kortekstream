# Struktur API untuk KortekStream Django

Dokumen ini menjelaskan struktur JSON yang **WAJIB** diikuti oleh semua API yang terintegrasi dengan Django KortekStream.

## 1. Prinsip Utama

### 1.1. Format Response Standar
Semua API **HARUS** mengembalikan response dalam format berikut:

```json
{
  "confidence_score": 1.0,
  "data": {
    // Data aktual di sini
  },
  "message": "Data berhasil diambil",
  "source": "gomunime.co"
}
```

### 1.2. Confidence Score
- **Wajib**: Setiap response harus memiliki `confidence_score` (float 0.0 - 1.0)
- **1.0**: Data lengkap dan akurat
- **0.5-0.9**: Data mungkin tidak lengkap
- **< 0.5**: Data sangat tidak lengkap atau bermasalah

### 1.3. Error Response
```json
{
  "error": true,
  "message": "Gagal mengambil data: Timeout",
  "confidence_score": 0.0
}
```

## 2. Endpoint dan Struktur JSON

### 2.1. GET `/api/v1/home`

**Response Sukses:**
```json
{
  "confidence_score": 1.0,
  "data": {
    "top10": [
      {
        "judul": "One Piece",
        "url": "https://gomunime.co/anime/one-piece/",
        "anime_slug": "one-piece",
        "rating": "8.73",
        "cover": "https://gomunime.co/wp-content/uploads/2020/04/E5RxYkWX0AAwdGH.png.jpg",
        "genres": ["Anime"]
      }
    ],
    "new_eps": [
      {
        "judul": "Zutaboro Reijou wa Ane no Moto",
        "url": "https://gomunime.co/anime/zutaboro-reijou-wa-ane-no-moto/",
        "anime_slug": "zutaboro-reijou-wa-ane-no-moto",
        "episode": "5",
        "rilis": "5 hours yang lalu",
        "cover": "https://gomunime.co/wp-content/uploads/2025/08/Zutaboro-Reijou-wa-Ane-no-Moto-Episode-5.jpg"
      }
    ],
    "movies": [
      {
        "judul": "Sidonia no Kishi Ai Tsumugu Hoshi",
        "url": "https://gomunime.co/anime/sidonia-no-kishi-ai-tsumugu-hoshi/",
        "anime_slug": "sidonia-no-kishi-ai-tsumugu-hoshi",
        "tanggal": "Jun 4, 2021",
        "cover": "https://gomunime.co/wp-content/uploads/2025/07/108354.jpg",
        "genres": ["Action", "Sci-Fi"]
      }
    ],
    "jadwal_rilis": {
      "Monday": [
        {
          "title": "Busamen Gachi Fighter",
          "url": "https://gomunime.co/anime/busamen-gachi-fighter/",
          "anime_slug": "busamen-gachi-fighter",
          "cover_url": "https://gomunime.co/wp-content/uploads/2025/07/150515.jpg",
          "type": "TV",
          "score": "6.68",
          "genres": ["Action", "Adventure"],
          "release_time": "00:00"
        }
      ],
      "Tuesday": [],
      "Wednesday": [],
      "Thursday": [],
      "Friday": [],
      "Saturday": [],
      "Sunday": []
    }
  }
}
```

### 2.2. GET `/api/v1/anime-terbaru?page=<int>`

**Response Sukses:**
```json
{
  "confidence_score": 1.0,
  "data": [
    {
      "judul": "Zutaboro Reijou wa Ane no Moto",
      "url": "https://gomunime.co/anime/zutaboro-reijou-wa-ane-no-moto/",
      "anime_slug": "zutaboro-reijou-wa-ane-no-moto",
      "episode": "5",
      "uploader": "Urusai",
      "rilis": "5 hours yang lalu",
      "cover": "https://gomunime.co/wp-content/uploads/2025/08/Zutaboro-Reijou-wa-Ane-no-Moto-Episode-5.jpg"
    }
  ]
}
```

### 2.3. GET `/api/v1/movie?page=<int>`

**Response Sukses:**
```json
{
  "confidence_score": 1.0,
  "data": [
    {
      "judul": "Sidonia no Kishi Ai Tsumugu Hoshi",
      "url": "https://gomunime.co/anime/sidonia-no-kishi-ai-tsumugu-hoshi/",
      "anime_slug": "sidonia-no-kishi-ai-tsumugu-hoshi",
      "status": "Completed",
      "skor": "7.45",
      "sinopsis": "Setelah Bumi dihancurkan oleh alien yang disebut dengan Gauna...",
      "views": "477265 Views",
      "cover": "https://gomunime.co/wp-content/uploads/2025/07/108354.jpg",
      "genres": ["Action", "Sci-Fi"],
      "tanggal": "N/A"
    }
  ]
}
```

### 2.4. GET `/api/v1/jadwal-rilis`

**Response Sukses:**
```json
{
  "confidence_score": 1.0,
  "data": {
    "Monday": [
      {
        "title": "Busamen Gachi Fighter",
        "url": "https://gomunime.co/anime/busamen-gachi-fighter/",
        "anime_slug": "busamen-gachi-fighter",
        "cover_url": "https://gomunime.co/wp-content/uploads/2025/07/150515.jpg",
        "type": "TV",
        "score": "6.68",
        "genres": ["Action", "Adventure"],
        "release_time": "00:00"
      }
    ],
    "Tuesday": [],
    "Wednesday": [],
    "Thursday": [],
    "Friday": [],
    "Saturday": [],
    "Sunday": []
  }
}
```

### 2.5. GET `/api/v1/jadwal-rilis/<day>`

**Response Sukses:**
```json
{
  "confidence_score": 1.0,
  "data": [
    {
      "title": "Busamen Gachi Fighter",
      "url": "https://gomunime.co/anime/busamen-gachi-fighter/",
      "anime_slug": "busamen-gachi-fighter",
      "cover_url": "https://gomunime.co/wp-content/uploads/2025/07/150515.jpg",
      "type": "TV",
      "score": "6.68",
      "genres": ["Action", "Adventure"],
      "release_time": "00:00"
    }
  ]
}
```

### 2.6. GET `/api/v1/anime-detail?anime_slug=<string>`

**Response Sukses:**
```json
{
  "confidence_score": 1.0,
  "data": {
    "judul": "Nonton Anime Haikyuu!! Movie: Gomisuteba no Kessen",
    "url_anime": "https://gomunime.co/anime/haikyuu-movie-gomisuteba-no-kessen/",
    "anime_slug": "haikyuu-movie-gomisuteba-no-kessen",
    "url_cover": "https://gomunime.co/wp-content/uploads/2024/10/140360.jpg",
    "episode_list": [
      {
        "episode": "1",
        "title": "Haikyuu Movie: Gomisuteba no Kessen",
        "url": "https://gomunime.co/haikyuu-gomisuteba-no-kessen/",
        "episode_slug": "haikyuu-gomisuteba-no-kessen",
        "release_date": "31 October 2024"
      }
    ],
    "recommendations": [
      {
        "title": "Re:Zero kara Hajimeru Isekai Seikatsu Season 2",
        "url": "https://gomunime.co/anime/rezero-kara-hajimeru-isekai-seikatsu-season-2/",
        "anime_slug": "rezero-kara-hajimeru-isekai-seikatsu-season-2",
        "cover_url": "https://gomunime.co/wp-content/uploads/2020/07/108005.jpg",
        "rating": "8.79",
        "episode": "Eps 13"
      }
    ],
    "status": "Completed",
    "tipe": "Movie",
    "skor": "8.65",
    "penonton": "N/A",
    "sinopsis": "Kozume Kenma tidak pernah menganggap...",
    "genre": ["School", "Sports"],
    "details": {
      "Japanese": "ハイキュー!! ゴミ捨て場の決戦",
      "English": "Haikyuu!! The Dumpster Battle",
      "Status": "Completed",
      "Type": "Movie",
      "Source": "Manga",
      "Duration": "1 hr. 25 min.",
      "Total Episode": "1",
      "Season": "Movie",
      "Studio": "Production I.G",
      "Producers": "Dentsu, Mainichi Broadcasting System, Shueisha",
      "Released": "Feb 16, 2024"
    },
    "rating": {
      "score": "8.65",
      "users": "34,719"
    }
  }
}
```

### 2.7. GET `/api/v1/episode-detail?episode_url=<string>`

**Response Sukses:**
```json
{
  "confidence_score": 1.0,
  "data": {
    "title": "Haikyuu Movie: Gomisuteba no Kessen Sub Indo",
    "thumbnail_url": "https://gomunime.co/wp-content/uploads/2024/10/140360.jpg",
    "streaming_servers": [
      {
        "server_name": "Nakama 1080p",
        "streaming_url": "https://pixeldrain.com/api/file/7oKMEmKt"
      },
      {
        "server_name": "Nakama 360p",
        "streaming_url": "https://pixeldrain.com/api/file/SiFZpBKR"
      }
    ],
    "release_info": "5 months yang lalu",
    "download_links": {
      "MKV": {
        "360p": [
          {
            "provider": "Gofile",
            "url": "https://gofile.io/d/6gNJq6"
          }
        ],
        "480p": [],
        "720p": [],
        "1080p": []
      },
      "MP4": {
        "360p": [],
        "480p": [],
        "MP4HD": [],
        "FULLHD": []
      }
    },
    "navigation": {
      "previous_episode_url": "#",
      "all_episodes_url": "https://gomunime.co/anime/haikyuu-movie-gomisuteba-no-kessen/",
      "next_episode_url": null
    },
    "anime_info": {
      "title": "Haikyuu!! Movie: Gomisuteba no Kessen",
      "thumbnail_url": "https://gomunime.co/wp-content/uploads/2024/10/140360.jpg",
      "synopsis": "Kozume Kenma tidak pernah menganggap...",
      "genres": ["School", "Sports"]
    },
    "other_episodes": [
      {
        "title": "Haikyuu Movie: Gomisuteba no Kessen",
        "url": "https://gomunime.co/haikyuu-gomisuteba-no-kessen/",
        "thumbnail_url": "https://gomunime.co/wp-content/uploads/2024/10/Haikyu.The_.Dumpster.Battle.jpg",
        "release_date": "31 October 2024"
      }
    ]
  }
}
```

### 2.8. GET `/api/v1/search?query=<string>`

**Response Sukses:**
```json
{
  "confidence_score": 1.0,
  "data": [
    {
      "judul": "Naruto Kecil",
      "url_anime": "https://gomunime.co/anime/naruto-kecil/",
      "anime_slug": "naruto-kecil",
      "status": "Completed",
      "tipe": "TV",
      "skor": "8.84",
      "penonton": "154157 Views",
      "sinopsis": "Beberapa saat sebelum Naruto Uzumaki lahir...",
      "genre": ["Action", "Adventure", "Fantasy", "Martial Arts", "Shounen"],
      "url_cover": "https://gomunime.co/wp-content/uploads/2024/08/142503.jpg"
    }
  ]
}
```

### 2.9. GET `/health`

**Response Sukses:**
```json
{
  "status": "ok"
}
```

## 3. Perbaikan untuk API Gomunime

### 3.1. Masalah yang Ditemukan
1. **Struktur JSON tidak konsisten**: Beberapa endpoint mengembalikan data langsung, beberapa dengan wrapper `data`
2. **Confidence score tidak ada**: API tidak mengembalikan `confidence_score`
3. **URL domain hardcoded**: Masih menggunakan domain lama

### 3.2. Perbaikan yang Diperlukan

#### A. Tambahkan Confidence Score
Semua endpoint harus mengembalikan `confidence_score`:

```go
type BaseResponse struct {
    ConfidenceScore float64 `json:"confidence_score"`
    Data            interface{} `json:"data"`
    Message         string `json:"message,omitempty"`
    Source          string `json:"source,omitempty"`
}
```

#### B. Standardisasi Response Format
Semua endpoint harus menggunakan format yang sama:

```go
func createSuccessResponse(data interface{}, confidence float64) gin.H {
    return gin.H{
        "confidence_score": confidence,
        "data": data,
        "message": "Data berhasil diambil",
        "source": "gomunime.co",
    }
}
```

#### C. Perbaiki URL Domain
Ganti semua URL dari domain lama ke `gomunime.co`:

```go
const BaseDomain = "https://gomunime.co"
```

## 4. Implementasi Fallback Logic yang Diperbaiki

### 4.1. Masalah Fallback Saat Ini
1. **Endpoint status tidak terupdate otomatis**: API yang down masih dianggap aktif
2. **Cache tidak dibersihkan**: Data lama masih digunakan
3. **Confidence score tidak diperiksa**: Fallback tidak berdasarkan kualitas data

### 4.2. Perbaikan Fallback Logic

#### A. Auto-Detection API Status
```python
def check_endpoint_health(endpoint):
    """Check if endpoint is actually working"""
    try:
        response = requests.get(f"{endpoint.url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False
```

#### B. Confidence Score Based Fallback
```python
def should_fallback(response_data, confidence_threshold=0.5):
    """Check if we should fallback based on confidence score"""
    if not response_data:
        return True
    
    confidence = response_data.get('confidence_score', 0)
    return confidence < confidence_threshold
```

#### C. Automatic Cache Clearing
```python
def clear_cache_on_failure(endpoint_name):
    """Clear cache when endpoint fails"""
    cache_keys = [
        f"api_response_{endpoint_name}",
        f"api_endpoints",
        f"template_filter_source_domain"
    ]
    for key in cache_keys:
        cache.delete(key)
```

## 5. Testing Checklist

### 5.1. API Endpoint Testing
- [ ] `/health` returns `{"status": "ok"}`
- [ ] All endpoints return `confidence_score`
- [ ] All endpoints use consistent JSON structure
- [ ] URLs use correct domain (`gomunime.co`)
- [ ] Error responses follow standard format

### 5.2. Fallback Testing
- [ ] System falls back when API is down
- [ ] System falls back when confidence_score < 0.5
- [ ] Cache is cleared on failure
- [ ] Source domain updates correctly
- [ ] All pages display content from fallback API

### 5.3. Integration Testing
- [ ] Homepage displays content
- [ ] Anime terbaru page works
- [ ] Detail episode page works
- [ ] Search functionality works
- [ ] Movie list page works
- [ ] Jadwal rilis page works

## 6. Deployment Instructions

### 6.1. Update API Gomunime
1. Update Go code to use new JSON structure
2. Add confidence score calculation
3. Update domain URLs
4. Test all endpoints

### 6.2. Update Django Fallback Logic
1. Implement improved health checking
2. Add confidence score based fallback
3. Improve cache management
4. Test fallback scenarios

### 6.3. Database Updates
1. Update API endpoints in Django admin
2. Set correct priorities
3. Verify source domains
4. Test monitoring dashboard 