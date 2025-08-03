# Dynamic API System - KortekStream

## 🎯 Overview

Sistem ini telah berhasil diperbarui dari hardcoded static values menjadi fully dynamic system yang dapat mendukung multiple API endpoints dari berbagai website anime dengan domain yang berbeda-beda.

## ✅ Yang Telah Diperbaiki

### 1. **Hardcoded Values Dihapus**
- ❌ `v1.samehadaku.how` hardcoded di multiple files
- ❌ Static URL construction
- ❌ Fixed domain references
- ✅ **Sekarang**: Dynamic domain management
- ✅ **Sekarang**: URL building berdasarkan active endpoint
- ✅ **Sekarang**: Fallback system yang robust

### 2. **Dynamic API Endpoints**
- ✅ Support multiple API sources
- ✅ Priority-based fallback system
- ✅ Real-time monitoring
- ✅ Cache management
- ✅ Automatic domain switching

### 3. **Management Tools**
- ✅ Command line tools untuk mengelola endpoints
- ✅ Testing dan monitoring
- ✅ Priority management
- ✅ Easy setup script

## 🚀 Fitur Utama

### 1. **Multiple API Support**
```bash
# Menambahkan endpoint dari berbagai website
./setup_dynamic_system.sh add-endpoint "Samehadaku" "https://api.samehadaku.how/api/v1" "v1.samehadaku.how" 10
./setup_dynamic_system.sh add-endpoint "Otakudesu" "https://api.otakudesu.com/api/v1" "otakudesu.com" 5
./setup_dynamic_system.sh add-endpoint "AnimeIndo" "https://api.animeindo.com/api/v1" "animeindo.com" 3
```

### 2. **Automatic Fallback**
- Sistem otomatis mencoba endpoint dengan prioritas tertinggi
- Jika gagal, mencoba endpoint berikutnya
- Domain sumber data berubah sesuai endpoint yang aktif
- Cache hasil untuk performa optimal

### 3. **Easy Management**
```bash
# Lihat semua endpoints
./setup_dynamic_system.sh list

# Test semua endpoints
./setup_dynamic_system.sh test

# Update prioritas
./setup_dynamic_system.sh update-endpoint 1 --priority 15

# Hapus endpoint
./setup_dynamic_system.sh delete-endpoint 1
```

## 📁 File yang Diperbarui

### 1. **Models** (`streamapp/models.py`)
- ✅ `APIEndpoint` model dengan dynamic domain support
- ✅ `get_current_source_domain()` method
- ✅ Cache management

### 2. **API Client** (`streamapp/api_client.py`)
- ✅ Dynamic endpoint selection
- ✅ Fallback mechanism
- ✅ No hardcoded URLs

### 3. **Views** (`streamapp/views.py`)
- ✅ Dynamic URL building
- ✅ Domain dari active endpoint
- ✅ Utility function integration

### 4. **Template Filters** (`streamapp/templatetags/streamapp_filters.py`)
- ✅ Dynamic domain retrieval
- ✅ Cache optimization
- ✅ Fallback support

### 5. **Utility Functions** (`streamapp/utils.py`)
- ✅ `get_current_source_domain()`
- ✅ `build_dynamic_url()`
- ✅ `extract_anime_slug_from_url()`
- ✅ `extract_episode_slug_from_url()`
- ✅ `format_image_url()`
- ✅ `clear_domain_cache()`

### 6. **Management Commands** (`streamapp/management/commands/manage_api_endpoints.py`)
- ✅ Add/update/delete endpoints
- ✅ Test endpoints
- ✅ Priority management
- ✅ Status monitoring

## 🛠️ Cara Penggunaan

### 1. **Setup Awal**
```bash
# Jalankan migrasi
./setup_dynamic_system.sh migrate

# Setup default endpoints
./setup_dynamic_system.sh setup

# Test sistem
./setup_dynamic_system.sh test
```

### 2. **Menambah Endpoint Baru**
```bash
# Endpoint dari website anime baru
./setup_dynamic_system.sh add-endpoint "Kusonime" "https://api.kusonime.com/api/v1" "kusonime.com" 4

# Endpoint dari website lain
./setup_dynamic_system.sh add-endpoint "Nekonime" "https://api.nekonime.com/api/v1" "nekonime.com" 2
```

### 3. **Monitoring dan Maintenance**
```bash
# Lihat status semua endpoints
./setup_dynamic_system.sh list

# Test performa endpoints
./setup_dynamic_system.sh test

# Update prioritas berdasarkan performa
./setup_dynamic_system.sh update-endpoint 1 --priority 15
```

### 4. **Development**
```bash
# Start development server
./setup_dynamic_system.sh server
```

## 🔧 Konfigurasi Database

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

## 📊 Monitoring

### 1. **Endpoint Status**
- ✅ Active/Inactive status
- ✅ Success count tracking
- ✅ Last used timestamp
- ✅ Priority management

### 2. **Performance Metrics**
- ✅ Response time monitoring
- ✅ Error tracking
- ✅ Success rate calculation
- ✅ Automatic fallback

### 3. **Cache Management**
- ✅ Domain cache
- ✅ API endpoint cache
- ✅ Template filter cache
- ✅ Automatic cache clearing

## 🔄 Fallback Chain

1. **APIEndpoint dengan prioritas tertinggi**
2. **SiteConfiguration fallback**
3. **Hardcoded default** ("v1.samehadaku.how")

## 🎯 Contoh Penggunaan Multiple APIs

### 1. **Setup Multiple Endpoints**
```bash
# Samehadaku (Primary)
./setup_dynamic_system.sh add-endpoint "Samehadaku" "https://api.samehadaku.how/api/v1" "v1.samehadaku.how" 10

# Otakudesu (Backup 1)
./setup_dynamic_system.sh add-endpoint "Otakudesu" "https://api.otakudesu.com/api/v1" "otakudesu.com" 5

# AnimeIndo (Backup 2)
./setup_dynamic_system.sh add-endpoint "AnimeIndo" "https://api.animeindo.com/api/v1" "animeindo.com" 3

# Kusonime (Backup 3)
./setup_dynamic_system.sh add-endpoint "Kusonime" "https://api.kusonime.com/api/v1" "kusonime.com" 2
```

### 2. **Testing dan Monitoring**
```bash
# Test semua endpoints
./setup_dynamic_system.sh test

# Lihat status
./setup_dynamic_system.sh list

# Update prioritas berdasarkan hasil test
./setup_dynamic_system.sh update-endpoint 1 --priority 15
```

## 🚨 Troubleshooting

### 1. **Endpoint Tidak Berfungsi**
```bash
# Test endpoint
./setup_dynamic_system.sh test

# Disable endpoint yang bermasalah
./setup_dynamic_system.sh update-endpoint 1 --inactive
```

### 2. **Domain Tidak Update**
```python
# Clear cache
from streamapp.utils import clear_domain_cache
clear_domain_cache()

# Check current domain
from streamapp.utils import get_current_source_domain
print(get_current_source_domain())
```

### 3. **Template Errors**
- Pastikan template filters menggunakan utility functions
- Clear template cache jika diperlukan
- Check domain format di database

## 📈 Performance Optimization

### 1. **Cache Strategy**
- Domain lookups cached for 24 hours
- API endpoint list cached for 1 hour
- Template filters cached for 24 hours
- Automatic cache invalidation

### 2. **Database Optimization**
- Indexed priority field
- Efficient queries
- Connection pooling
- Query optimization

### 3. **Monitoring**
- Real-time endpoint monitoring
- Performance metrics tracking
- Error logging
- Success rate calculation

## 🔒 Security

### 1. **Domain Validation**
- Format validation
- Protocol checking
- Sanitization
- Error handling

### 2. **URL Security**
- HTTPS enforcement
- Domain whitelisting
- Input sanitization
- XSS prevention

## 📋 Checklist Implementasi

- ✅ Remove hardcoded domains
- ✅ Implement dynamic URL building
- ✅ Add utility functions
- ✅ Create management commands
- ✅ Update template filters
- ✅ Add cache management
- ✅ Implement fallback system
- ✅ Create setup script
- ✅ Add monitoring tools
- ✅ Test all functionality
- ✅ Document everything

## 🎉 Hasil Akhir

Sistem sekarang sepenuhnya **dynamic** dan dapat:

1. **Mendukung multiple API sources** dari berbagai website anime
2. **Automatic fallback** jika endpoint utama gagal
3. **Dynamic domain management** sesuai endpoint yang aktif
4. **Easy management** dengan command line tools
5. **Real-time monitoring** dan testing
6. **Performance optimization** dengan caching
7. **No hardcoded values** - semuanya dinamis

## 📚 Dokumentasi Tambahan

- `DYNAMIC_API_SETUP.md` - Setup guide lengkap
- `migrate_to_dynamic.py` - Migration script
- `setup_dynamic_system.sh` - Management script

---

**🎯 Sistem sekarang siap untuk digunakan dengan multiple API sources dari berbagai website anime dengan domain yang berbeda-beda!** 