# Pengujian Integrasi KortekStream

Dokumen ini menjelaskan cara menjalankan pengujian integrasi untuk aplikasi KortekStream.

## Struktur Pengujian

Pengujian integrasi terdiri dari beberapa komponen:

1. **Pengujian Koneksi API** (`test_api_connection.py`): Menguji koneksi antara aplikasi Django dan FastAPI API.
2. **Pengujian Django Views** (`test_django_views.py`): Menguji fungsi view Django yang menggunakan API client.
3. **Runner Pengujian** (`run_integration_tests.py`): Skrip utama untuk menjalankan semua tes integrasi.

## Prasyarat

Sebelum menjalankan pengujian, pastikan:

1. Aplikasi FastAPI berjalan di `http://localhost:8000` (atau sesuai konfigurasi di `API_BASE_URL` di `streamapp/api_client.py`).
2. Lingkungan Django dikonfigurasi dengan benar.
3. Semua dependensi terinstal.

## Cara Menjalankan Pengujian

### Menjalankan Semua Pengujian

```bash
python tests/run_integration_tests.py
```

### Menjalankan Hanya Pengujian API

```bash
python tests/run_integration_tests.py --api-only
```

### Menjalankan Hanya Pengujian Views

```bash
python tests/run_integration_tests.py --views-only
```

## Hasil Pengujian

Hasil pengujian akan ditampilkan di konsol dan juga dicatat dalam file `integration_tests.log`. Setiap pengujian akan menampilkan status keberhasilan atau kegagalan, serta detail tambahan jika terjadi error.

## Apa yang Diuji

### Pengujian Koneksi API

- `get_home_data`: Menguji pengambilan data halaman utama.
- `get_anime_terbaru`: Menguji pengambilan data anime terbaru.
- `get_anime_detail`: Menguji pengambilan detail anime.
- `get_episode_detail`: Menguji pengambilan detail episode.
- `get_jadwal_rilis`: Menguji pengambilan jadwal rilis.
- `get_movie_list`: Menguji pengambilan daftar movie.
- `search_anime`: Menguji pencarian anime.

### Pengujian Django Views

- `index`: Menguji view halaman utama.
- `detail_anime`: Menguji view detail anime.
- `all_list_anime_terbaru`: Menguji view daftar anime terbaru.
- `all_list_jadwal_rilis`: Menguji view jadwal rilis.
- `all_list_movie`: Menguji view daftar movie.
- `search`: Menguji view pencarian.

## Penanganan Error

Pengujian dirancang untuk menangani error dengan baik. Jika terjadi error, detail error akan dicatat dalam log. Pengujian akan terus berjalan meskipun ada error di salah satu komponen.

## Mekanisme Fallback

Aplikasi mengimplementasikan mekanisme fallback untuk menangani kasus ketika API tidak tersedia:

1. **Cache Stale**: Data cache lama digunakan jika API tidak tersedia.
2. **Data Default**: Jika tidak ada cache, data default kosong akan digunakan.

Pengujian integrasi memverifikasi bahwa mekanisme fallback ini berfungsi dengan benar.

## Pemecahan Masalah

Jika pengujian gagal, periksa:

1. Apakah FastAPI berjalan dan dapat diakses?
2. Apakah konfigurasi API_BASE_URL benar?
3. Apakah ada masalah jaringan?
4. Apakah ada perubahan dalam struktur data API?

Periksa file log `integration_tests.log` untuk detail lebih lanjut tentang error yang terjadi.