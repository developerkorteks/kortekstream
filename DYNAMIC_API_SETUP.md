# Dynamic API Setup Guide

## Overview

Sistem ini telah diperbarui untuk mendukung multiple API endpoints dari berbagai website dan domain yang berbeda secara dinamis. Tidak ada lagi hardcoded values yang statis.

## Fitur Utama

### 1. Dynamic API Endpoints
- Mendukung multiple API endpoints dari berbagai website
- Sistem prioritas untuk fallback otomatis
- Monitoring status API secara real-time
- Cache management untuk performa optimal

### 2. Dynamic Domain Management
- Domain sumber data dapat diubah secara dinamis
- Support untuk berbagai website anime scraping
- Fallback system yang robust
- URL formatting yang konsisten

### 3. Management Commands
- Command line tools untuk mengelola API endpoints
- Testing dan monitoring API status
- Priority management

## Setup dan Konfigurasi

### 1. Menambahkan API Endpoint Baru

```bash
# Menambahkan endpoint baru
python manage.py manage_api_endpoints add --name "Samehadaku API" --url "https://api.samehadaku.how/api/v1" --domain "v1.samehadaku.how" --priority 10 --active

# Menambahkan endpoint dari website lain
python manage.py manage_api_endpoints add --name "Otakudesu API" --url "https://api.otakudesu.com/api/v1" --domain "otakudesu.com" --priority 5 --active

# Menambahkan endpoint dari website ketiga
python manage.py manage_api_endpoints add --name "AnimeIndo API" --url "https://api.animeindo.com/api/v1" --domain "animeindo.com" --priority 3 --active
```

### 2. Melihat Daftar Endpoints

```bash
# Melihat semua endpoints
python manage.py manage_api_endpoints list

# Testing semua endpoints aktif
python manage.py manage_api_endpoints test

# Testing endpoint tertentu
python manage.py manage_api_endpoints test --id 1
```

### 3. Mengelola Prioritas

```bash
# Set prioritas endpoint
python manage.py manage_api_endpoints set-priority --id 1 --priority 15

# Update endpoint
python manage.py manage_api_endpoints update --id 1 --priority 20 --domain "new-domain.com"
```

## Struktur Database

### APIEndpoint Model
```python
class APIEndpoint(models.Model):
    name = models.CharField(max_length=100)  # Nama API
    url = models.URLField(max_length=255)    # URL API
    source_domain = models.CharField(max_length=255)  # Domain sumber data
    priority = models.IntegerField(default=0)  # Prioritas (semakin tinggi semakin diprioritaskan)
    is_active = models.BooleanField(default=True)  # Status aktif
    success_count = models.IntegerField(default=0)  # Jumlah sukses
    last_used = models.DateTimeField(null=True, blank=True)  # Terakhir digunakan
```

## Utility Functions

### 1. Domain Management
```python
from streamapp.utils import get_current_source_domain, build_dynamic_url

# Mendapatkan domain yang sedang aktif
domain = get_current_source_domain()

# Membuat URL dinamis
url = build_dynamic_url("anime/one-piece/")
```

### 2. URL Processing
```python
from streamapp.utils import extract_anime_slug_from_url, extract_episode_slug_from_url

# Ekstrak anime slug
anime_slug = extract_anime_slug_from_url("https://domain.com/anime/one-piece/")

# Ekstrak episode slug
episode_slug = extract_episode_slug_from_url("https://domain.com/one-piece-episode-1/")
```

### 3. Image URL Formatting
```python
from streamapp.utils import format_image_url

# Format image URL
image_url = format_image_url("/wp-content/uploads/image.jpg")
```

## Template Filters

### 1. extract_anime_slug
```django
{% with anime_slug=anime.url|extract_anime_slug %}
    <a href="{% url 'streamapp:detail_anime' anime_slug %}">{{ anime.title }}</a>
{% endwith %}
```

### 2. extract_episode_slug
```django
{% with episode_slug=episode.url|extract_episode_slug %}
    <a href="{% url 'streamapp:detail_episode_video' episode_slug %}">{{ episode.title }}</a>
{% endwith %}
```

### 3. format_url
```django
<img src="{{ anime.cover|format_url }}" alt="{{ anime.title }}">
```

## Contoh Penggunaan Multiple APIs

### 1. Setup Multiple Endpoints
```bash
# Endpoint utama (prioritas tinggi)
python manage.py manage_api_endpoints add --name "Samehadaku Primary" --url "https://api.samehadaku.how/api/v1" --domain "v1.samehadaku.how" --priority 10 --active

# Endpoint backup 1
python manage.py manage_api_endpoints add --name "Otakudesu Backup" --url "https://api.otakudesu.com/api/v1" --domain "otakudesu.com" --priority 5 --active

# Endpoint backup 2
python manage.py manage_api_endpoints add --name "AnimeIndo Backup" --url "https://api.animeindo.com/api/v1" --domain "animeindo.com" --priority 3 --active
```

### 2. Monitoring Status
```bash
# Test semua endpoints
python manage.py manage_api_endpoints test

# Lihat status
python manage.py manage_api_endpoints list
```

### 3. Fallback System
Sistem akan otomatis:
1. Mencoba endpoint dengan prioritas tertinggi
2. Jika gagal, mencoba endpoint berikutnya
3. Update domain sumber data sesuai endpoint yang aktif
4. Cache hasil untuk performa optimal

## Cache Management

### 1. Clear Cache
```python
from streamapp.utils import clear_domain_cache

# Clear semua cache domain
clear_domain_cache()
```

### 2. Cache Keys
- `api_endpoints`: Cache untuk daftar API endpoints
- `template_filter_source_domain`: Cache untuk domain di template filters
- `view_cache_*`: Cache untuk view functions

## Error Handling

### 1. Fallback Chain
1. APIEndpoint dengan prioritas tertinggi
2. SiteConfiguration fallback
3. Hardcoded default ("v1.samehadaku.how")

### 2. Logging
```python
import logging
logger = logging.getLogger(__name__)

# Log error saat endpoint gagal
logger.error(f"Endpoint {endpoint.name} failed: {error}")
```

## Best Practices

### 1. Domain Management
- Selalu set `source_domain` saat menambah endpoint baru
- Gunakan domain yang valid dan konsisten
- Test endpoint sebelum mengaktifkan

### 2. Priority Management
- Set prioritas berdasarkan reliability dan speed
- Monitor success_count untuk evaluasi
- Update prioritas berdasarkan performa

### 3. Monitoring
- Regular testing dengan `manage_api_endpoints test`
- Monitor log untuk error patterns
- Update endpoints yang tidak reliable

## Troubleshooting

### 1. Endpoint Tidak Berfungsi
```bash
# Test endpoint
python manage.py manage_api_endpoints test --id 1

# Check logs
tail -f logs/django.log

# Disable endpoint yang bermasalah
python manage.py manage_api_endpoints update --id 1 --inactive
```

### 2. Domain Tidak Update
```python
# Clear cache
from streamapp.utils import clear_domain_cache
clear_domain_cache()

# Check current domain
from streamapp.utils import get_current_source_domain
print(get_current_source_domain())
```

### 3. Template Errors
- Pastikan template filters menggunakan utility functions
- Clear template cache jika diperlukan
- Check domain format di database

## Migration dari Sistem Lama

### 1. Backup Data
```bash
# Backup database
python manage.py dumpdata streamapp.APIEndpoint > api_endpoints_backup.json
```

### 2. Update Existing Endpoints
```bash
# Update endpoint yang ada
python manage.py manage_api_endpoints update --id 1 --domain "new-domain.com" --priority 10
```

### 3. Test System
```bash
# Test semua endpoints
python manage.py manage_api_endpoints test

# Test website
python manage.py runserver
```

## Monitoring dan Maintenance

### 1. Regular Tasks
- Test endpoints setiap hari
- Monitor success_count
- Update prioritas berdasarkan performa
- Clear cache jika diperlukan

### 2. Performance Optimization
- Cache domain lookups
- Use connection pooling
- Monitor response times
- Optimize database queries

### 3. Security
- Validate domain formats
- Sanitize URLs
- Monitor for suspicious activities
- Regular security updates

## Contoh Konfigurasi Lengkap

### 1. Multiple Anime Websites
```bash
# Samehadaku (Primary)
python manage.py manage_api_endpoints add --name "Samehadaku" --url "https://api.samehadaku.how/api/v1" --domain "v1.samehadaku.how" --priority 10 --active

# Otakudesu (Backup 1)
python manage.py manage_api_endpoints add --name "Otakudesu" --url "https://api.otakudesu.com/api/v1" --domain "otakudesu.com" --priority 5 --active

# AnimeIndo (Backup 2)
python manage.py manage_api_endpoints add --name "AnimeIndo" --url "https://api.animeindo.com/api/v1" --domain "animeindo.com" --priority 3 --active

# Kusonime (Backup 3)
python manage.py manage_api_endpoints add --name "Kusonime" --url "https://api.kusonime.com/api/v1" --domain "kusonime.com" --priority 2 --active
```

### 2. Testing Setup
```bash
# Test semua endpoints
python manage.py manage_api_endpoints test

# Lihat status
python manage.py manage_api_endpoints list

# Set prioritas berdasarkan hasil test
python manage.py manage_api_endpoints set-priority --id 1 --priority 15
```

Sistem ini sekarang sepenuhnya dinamis dan dapat mendukung multiple API sources dari berbagai website anime dengan domain yang berbeda-beda. 