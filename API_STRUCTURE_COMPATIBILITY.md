# API Structure Compatibility Guide

## **Perbedaan Struktur JSON antara Gomunime dan Samehadaku**

### **1. Gomunime API Structure (Wrapper Format)**
```json
{
  "confidence_score": 1,
  "data": {
    "top10": [...],
    "new_eps": [...],
    "movies": [...],
    "jadwal_rilis": {...}
  }
}
```

### **2. Samehadaku API Structure (Direct Format)**
```json
{
  "confidence_score": 1.0,
  "top10": [...],
  "new_eps": [...],
  "movies": [...],
  "jadwal_rilis": {...}
}
```

## **Perbedaan Utama:**

| Aspek | Gomunime | Samehadaku |
|-------|----------|------------|
| **Data Wrapper** | Ada field `"data"` | Tidak ada wrapper |
| **Confidence Score** | Integer (1) | Float (1.0) |
| **Field Names** | Sama | Sama |
| **Data Structure** | Nested dalam `data` | Direct access |

## **Solusi yang Diimplementasikan:**

### **1. Fungsi Normalisasi (`normalize_api_response`)**
```python
def normalize_api_response(data: Any, endpoint_name: str = "unknown") -> Any:
    """
    Normalize API response to handle different JSON structures.
    """
    if not data:
        return data
    
    # Jika data adalah dict dan memiliki confidence_score
    if isinstance(data, dict) and 'confidence_score' in data:
        confidence = data.get('confidence_score', 0)
        logger.info(f"API {endpoint_name} response with confidence score: {confidence}")
        
        # Jika ada field 'data', gunakan itu (gomunime format)
        if 'data' in data:
            logger.info(f"Using gomunime format (with 'data' wrapper) for {endpoint_name}")
            return data.get('data', {})
        # Jika tidak ada field 'data', gunakan data langsung (samehadaku format)
        else:
            logger.info(f"Using samehadaku format (direct data) for {endpoint_name}")
            return data
    
    # Jika data bukan dict atau tidak memiliki confidence_score, kembalikan as-is
    return data
```

### **2. Fungsi yang Sudah Diperbaiki:**

#### **Home Data (`get_home_data`)**
- ✅ Mendukung kedua format
- ✅ Normalisasi otomatis
- ✅ Logging untuk debugging

#### **Anime Terbaru (`get_anime_terbaru`)**
- ✅ Mendukung kedua format
- ✅ Normalisasi otomatis
- ✅ Fallback ke samehadaku jika gomunime down

#### **Movie List (`get_movie_list`)**
- ✅ Mendukung kedua format
- ✅ Normalisasi otomatis
- ✅ Fallback ke samehadaku jika gomunime down

#### **Anime Detail (`get_anime_detail`)**
- ✅ Mendukung kedua format
- ✅ Normalisasi otomatis
- ✅ Error handling yang robust

#### **Episode Detail (`get_episode_detail`)**
- ✅ Mendukung kedua format
- ✅ Normalisasi otomatis
- ✅ Error handling yang robust

#### **Search (`search_anime`)**
- ✅ Mendukung kedua format
- ✅ Normalisasi otomatis
- ✅ Fallback ke samehadaku jika gomunime down

#### **Jadwal Rilis (`get_jadwal_rilis`)**
- ✅ Mendukung kedua format
- ✅ Normalisasi otomatis
- ✅ Support untuk per-hari dan semua hari

## **Cara Kerja Sistem:**

### **1. Deteksi Format Otomatis**
```python
# Gomunime format
if 'data' in response:
    return response['data']  # Extract dari wrapper

# Samehadaku format
else:
    return response  # Gunakan langsung
```

### **2. Fallback System**
```python
# Priority: Gomunime (500) > Samehadaku (100)
# Jika gomunime down → otomatis ke samehadaku
# Jika gomunime up → kembali ke gomunime
```

### **3. Error Handling**
```python
# Jika kedua API down
return {
    "error": True,
    "message": "Semua API tidak tersedia",
    "data": []
}
```

## **Testing:**

### **Test Gomunime Format:**
```bash
curl -s "http://localhost:8080/api/v1/home" | jq '.confidence_score, .data'
```

### **Test Samehadaku Format:**
```bash
curl -s "https://wet-slide-hoj.domcloud.dev/api/v1/home/" | jq '.confidence_score, .top10'
```

## **Keuntungan Solusi Ini:**

1. **✅ Plug & Play**: Tidak perlu mengubah struktur API
2. **✅ Backward Compatible**: Mendukung format lama dan baru
3. **✅ Automatic Detection**: Deteksi format otomatis
4. **✅ Robust Fallback**: Fallback otomatis antar API
5. **✅ Detailed Logging**: Logging untuk debugging
6. **✅ Error Handling**: Error handling yang robust

## **Status Implementasi:**

- ✅ **Home Data**: Berfungsi dengan kedua API
- ✅ **Anime Terbaru**: Berfungsi dengan kedua API
- ✅ **Movie List**: Berfungsi dengan kedua API
- ✅ **Anime Detail**: Berfungsi dengan kedua API
- ✅ **Episode Detail**: Berfungsi dengan kedua API
- ✅ **Search**: Berfungsi dengan kedua API
- ✅ **Jadwal Rilis**: Berfungsi dengan kedua API

## **Kesimpulan:**

Sistem sekarang **100% kompatibel** dengan kedua format API (gomunime dan samehadaku) dan dapat beralih otomatis antara keduanya berdasarkan ketersediaan dan prioritas. 