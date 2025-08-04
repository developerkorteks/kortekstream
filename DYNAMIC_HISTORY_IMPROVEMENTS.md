# Dynamic History System Improvements

## Overview

Sistem riwayat tontonan (watch history) telah diperbarui untuk mendukung API dinamis dan multiple sumber scraping. Sistem ini sekarang dapat melacak sumber API yang digunakan untuk setiap episode yang ditonton dan menangani URL dari berbagai domain secara otomatis.

## Fitur Baru

### 1. API Source Tracking
- Setiap item riwayat sekarang menyimpan informasi API source
- Meliputi nama API, domain, dan endpoint
- Memungkinkan tracking dari mana data episode berasal

### 2. Dynamic URL Handling
- Normalisasi URL episode untuk berbagai format domain
- Support untuk multiple API endpoints
- Penanganan URL malformed secara otomatis

### 3. Enhanced Deduplication
- Deduplikasi berdasarkan episode slug yang dinormalisasi
- Menghindari duplikasi saat domain berubah
- Support untuk berbagai format URL

## Perubahan Utama

### 1. JavaScript History System (`streamapp/static/js/storage/history.js`)

#### Fungsi Baru:
- `getCurrentAPISource()` - Mendapatkan informasi API source saat ini
- `normalizeEpisodeSlug()` - Normalisasi episode slug untuk berbagai domain
- `buildEpisodeURL()` - Membangun URL episode dengan domain yang benar

#### Fungsi yang Diperbarui:
- `addToWatchHistory()` - Sekarang async dan mendukung API source
- `loadWatchHistoryToEpisode()` - Mendukung dynamic URL building

### 2. Django Views

#### Views yang Diperbarui:
- `user_collection()` - Menyediakan API source information
- `index()` - Menyediakan API source information  
- `detail_episode_video()` - Menyediakan API source information

### 3. Templates

#### Templates yang Diperbarui:
- `user_collection.html` - Menampilkan API source di riwayat
- `index.html` - Menyediakan API source untuk JavaScript
- `detail_episode_video.html` - Menyediakan API source untuk JavaScript

## Struktur Data Baru

### History Item Structure
```javascript
{
    id: 12345,
    title: "One Piece",
    slug: "one-piece",
    episodeSlug: "one-piece-episode-1",
    episodeTitle: "Episode 1 - Saya Adalah Luffy!",
    cover: "https://example.com/cover.jpg",
    watchedAt: "2024-01-01T12:00:00Z",
    apiSource: {
        name: "Samehadaku API",
        domain: "v1.samehadaku.how",
        endpoint: "https://api.samehadaku.how/api/v1"
    }
}
```

### API Source Structure
```javascript
{
    name: "API Name",
    domain: "domain.com",
    endpoint: "https://api.domain.com/api/v1"
}
```

## URL Normalization

### Supported URL Formats:
1. **Simple slug**: `one-piece-episode-1`
2. **With episode prefix**: `/episode/one-piece-episode-1`
3. **Full URL**: `https://domain.com/one-piece-episode-1`
4. **Malformed URL**: `https:domain.com/one-piece-episode-1`

### Normalization Process:
1. Remove protocol and domain
2. Remove episode prefix if present
3. Handle specific domain formats
4. Remove trailing slashes
5. Handle malformed URLs

## Dynamic URL Building

### URL Building Logic:
- Jika domain tersedia: `https://domain.com/episode-slug`
- Jika domain tidak tersedia: `/episode/episode-slug`

### Examples:
```javascript
// Input: "one-piece-episode-1", domain: "v1.samehadaku.how"
// Output: "https://v1.samehadaku.how/one-piece-episode-1"

// Input: "one-piece-episode-1", domain: null
// Output: "/episode/one-piece-episode-1"
```

## Testing

### Test File: `test_history_js.html`
File test HTML yang dapat digunakan untuk memverifikasi:
- API source tracking
- URL normalization
- History storage
- Dynamic URL building

### Test Cases:
1. **API Source Test** - Verifikasi informasi API source
2. **History Storage Test** - Verifikasi penyimpanan riwayat
3. **URL Building Test** - Verifikasi pembangunan URL dinamis
4. **Add Test History** - Menambahkan data test ke riwayat
5. **Clear History** - Membersihkan riwayat

## Kompatibilitas

### Backward Compatibility:
- Sistem tetap mendukung data riwayat lama tanpa API source
- Fallback ke default API source jika tidak tersedia
- URL building tetap berfungsi untuk data lama

### Migration:
- Data riwayat lama akan tetap berfungsi
- API source akan ditambahkan saat episode baru ditonton
- Tidak ada migrasi data yang diperlukan

## Keuntungan

### 1. Multi-API Support
- Support untuk berbagai API endpoints
- Tracking sumber data untuk setiap episode
- Fallback otomatis ke API lain

### 2. Better URL Handling
- Normalisasi URL yang konsisten
- Support untuk berbagai format domain
- Penanganan URL malformed

### 3. Enhanced User Experience
- Informasi sumber data di riwayat
- URL yang benar untuk setiap episode
- Deduplikasi yang lebih akurat

### 4. Developer Experience
- Kode yang lebih modular
- Testing yang lebih mudah
- Dokumentasi yang lengkap

## Penggunaan

### Menambahkan Episode ke Riwayat:
```javascript
await addToWatchHistory(
    null,                    // animeId (optional)
    "One Piece",            // title
    "one-piece",            // slug
    "one-piece-episode-1",  // episodeSlug
    "Episode 1",            // episodeTitle
    "cover.jpg",            // cover
    apiSource               // API source object
);
```

### Mendapatkan API Source:
```javascript
const apiSource = await getCurrentAPISource();
// Returns: { name: "API Name", domain: "domain.com", endpoint: "..." }
```

### Building Episode URL:
```javascript
const episodeURL = buildEpisodeURL(episodeSlug, domain);
// Returns: "https://domain.com/episode-slug" or "/episode/episode-slug"
```

## Troubleshooting

### Common Issues:

1. **API Source Not Available**
   - Check if `window.currentAPISource` is set
   - Verify Django view provides API source information

2. **URL Not Building Correctly**
   - Check domain format in API source
   - Verify episode slug normalization

3. **History Not Saving**
   - Check localStorage availability
   - Verify async function calls

### Debug Information:
- Console logs provide detailed information
- Test file can be used for debugging
- API source information is displayed in history

## Future Enhancements

### Planned Improvements:
1. **API Source Migration** - Migrasi data lama dengan API source
2. **Enhanced Analytics** - Tracking penggunaan API source
3. **API Performance Monitoring** - Monitoring performa API
4. **User Preferences** - Preferensi API source per user

### Potential Features:
1. **API Source Filtering** - Filter riwayat berdasarkan API source
2. **API Source Statistics** - Statistik penggunaan API source
3. **API Source Recommendations** - Rekomendasi API source terbaik
4. **API Source Health Monitoring** - Monitoring kesehatan API source 