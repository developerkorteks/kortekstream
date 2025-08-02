# Panduan Pengembangan API Web Scraping untuk KortekStream

Dokumen ini memberikan panduan dan rekomendasi untuk mengembangkan API web scraping eksternal yang akan digunakan oleh aplikasi Django KortekStream sebagai sumber data utama atau fallback.

## 1. Tujuan API

API ini bertanggung jawab untuk:
*   Melakukan web scraping dari berbagai situs web sumber (misalnya, situs anime, movie, jadwal rilis).
*   Memproses dan menstandardisasi data yang diambil.
*   Menyediakan data tersebut melalui endpoint HTTP yang konsisten dalam format JSON.
*   Menyediakan mekanisme fallback dan metrik kepercayaan (`confidence_score`) untuk integrasi yang mulus dengan aplikasi Django.

## 2. Pilihan Teknologi

Anda dapat memilih antara **Go** atau **FastAPI (Python)**, atau teknologi lain yang Anda kuasai, selama memenuhi prinsip-prinsip di bawah.

### Go (Rekomendasi untuk Performa Tinggi dan Konkurensi)
*   **Kelebihan:** Performa sangat tinggi, konkurensi bawaan (goroutine), binary mandiri (mudah deploy), cocok untuk operasi I/O-bound seperti scraping.
*   **Pustaka Umum:**
    *   HTTP Client: `net/http` (bawaan), `resty`
    *   HTML Parsing: `goquery`, `colly`
    *   JSON Handling: `encoding/json` (bawaan)
    *   Web Framework: `Gin`, `Echo`, `Fiber`
    *   Headless Browser: `chromedp` (untuk situs yang mengandalkan JavaScript)

### FastAPI (Rekomendasi untuk Pengembangan Cepat dan Ekosistem Python)
*   **Kelebihan:** Sangat cepat untuk dikembangkan, validasi data otomatis (Pydantic), dokumentasi API otomatis (Swagger UI), ekosistem pustaka scraping Python yang kaya.
*   **Pustaka Umum:**
    *   HTTP Client: `httpx`, `requests`
    *   HTML Parsing: `BeautifulSoup4`, `lxml`
    *   Headless Browser: `Playwright`, `Selenium`
    *   Asynchronous: `asyncio` (bawaan Python)

## 3. Struktur Proyek (Contoh)

### Untuk FastAPI (Python)
```
my_scraper_api/
├── main.py             # Inisialisasi FastAPI app, definisi router
├── config.py           # Pengaturan konfigurasi (URL sumber, timeout, dll.)
├── scrapers/           # Modul untuk logika scraping spesifik per situs
│   ├── __init__.py
│   ├── site_a_scraper.py
│   └── site_b_scraper.py
├── models/             # Definisi Pydantic models untuk input/output data
│   ├── __init__.py
│   └── data_models.py
├── api/                # Definisi endpoint API
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       ├── endpoints.py # Endpoint untuk anime-terbaru, movie, dll.
│       └── health.py    # Endpoint health check
└── utils/              # Fungsi utilitas (logging, proxy rotation, dll.)
    ├── __init__.py
    └── http_client.py
```

### Untuk Go
```
my_scraper_api/
├── main.go             # Inisialisasi server HTTP, router
├── config/             # Pengaturan konfigurasi
│   └── config.go
├── scrapers/           # Paket untuk logika scraping spesifik per situs
│   ├── site_a_scraper.go
│   └── site_b_scraper.go
├── api/                # Paket untuk handler API
│   ├── v1/
│   │   ├── endpoints.go # Handler untuk anime-terbaru, movie, dll.
│   │   └── health.go    # Handler health check
│   └── router.go
└── utils/              # Paket utilitas (logging, http client kustom, dll.)
    └── http_client.go
```

## 4. Prinsip Pengembangan Utama

### 4.1. Konsistensi Output Data
*   **Format JSON:** Semua respons API harus dalam format JSON.
*   **Struktur Data Standar:** Tentukan struktur JSON yang konsisten untuk setiap jenis data (anime, episode, movie, jadwal rilis, hasil pencarian). Ini sangat penting agar aplikasi Django dapat mengonsumsi data dengan mudah.
    *   **Pola Umum (dengan `data` wrapper):**
        ```json
        {
            "data": [...], // List of scraped items
            "confidence_score": 0.95, // Wajib: Skor kepercayaan data (0.0 - 1.0)
            "message": "Data berhasil diambil", // Opsional: Pesan status
            "source": "nama_situs_sumber" // Opsional: Situs sumber data
        }
        ```
    *   **Pola Alternatif (konten langsung di level teratas, seperti untuk jadwal rilis):**
        ```json
        {
            "confidence_score": 0.95, // Wajib: Skor kepercayaan data (0.0 - 1.0)
            "Monday": [...],
            "Tuesday": [...],
            // ... hari lainnya
            "message": "Data berhasil diambil", // Opsional: Pesan status
            "source": "nama_situs_sumber" // Opsional: Situs sumber data
        }
        ```
    *   **Catatan:** Pastikan `confidence_score` selalu ada di level teratas respons sukses.
*   **`confidence_score`:** Setiap respons API harus menyertakan `confidence_score` (float antara 0.0 dan 1.0). Ini menunjukkan seberapa yakin API terhadap kualitas dan kelengkapan data yang diambil.
    *   `1.0`: Data lengkap dan akurat.
    *   `0.5-0.9`: Data mungkin tidak lengkap atau ada anomali kecil.
    *   `< 0.5`: Data sangat tidak lengkap atau ada masalah signifikan.
    *   Aplikasi Django akan menggunakan skor ini untuk memutuskan apakah akan menggunakan data atau mencoba fallback ke API lain.

### 4.2. Penanganan Kesalahan yang Robust
*   **Kode Status HTTP:** Gunakan kode status HTTP yang sesuai (misalnya, `200 OK` untuk sukses, `404 Not Found` jika data tidak ada, `500 Internal Server Error` untuk kesalahan server, `503 Service Unavailable` jika situs sumber tidak dapat dijangkau).
*   **Pesan Kesalahan:** Sertakan pesan kesalahan yang jelas dalam respons JSON jika terjadi masalah.
    ```json
    {
        "error": true,
        "message": "Gagal mengambil data dari situs sumber: Timeout",
        "confidence_score": 0.0
    }
    ```
*   **Retry Logic:** Implementasikan logika retry dengan backoff eksponensial saat mencoba scraping dari situs sumber.
*   **Logging:** Log semua aktivitas penting, termasuk keberhasilan scraping, kegagalan, dan detail kesalahan.

### 4.3. Endpoint Health Check
*   Sediakan endpoint `/health` atau `/status` yang dapat diakses oleh aplikasi Django untuk memverifikasi bahwa API scraping berfungsi dengan baik.
*   Respons harus ringan dan cepat (misalnya, `{"status": "ok"}`).

### 4.4. Anti-Bot Measures & Rate Limiting
*   **User-Agent Rotation:** Gunakan berbagai User-Agent untuk menghindari deteksi.
*   **Proxy Rotation:** Pertimbangkan penggunaan proxy jika Anda melakukan scraping dalam skala besar untuk menghindari pemblokiran IP.
*   **Delay/Rate Limiting:** **Sangat penting** untuk menghormati `robots.txt` dan menerapkan penundaan antar permintaan ke situs sumber untuk menghindari pemblokiran dan meminimalkan beban pada server target. Jangan membanjiri situs.
*   **Headless Browsers:** Gunakan headless browser (seperti Chrome via `chromedp` di Go atau `Playwright`/`Selenium` di Python) jika situs target sangat mengandalkan JavaScript untuk merender konten.

### 4.5. Caching
*   Implementasikan caching di sisi API scraping untuk data yang sering diakses atau yang tidak sering berubah. Ini akan mengurangi beban pada situs sumber dan mempercepat respons API Anda.

### 4.6. Konfigurasi
*   Semua URL situs sumber, kunci API (jika ada), pengaturan timeout, dan konfigurasi lainnya harus dapat dikonfigurasi (misalnya, melalui variabel lingkungan atau file konfigurasi).

## 5. Endpoint yang Diharapkan oleh Django

Aplikasi Django KortekStream mengharapkan endpoint-endpoint berikut dengan struktur respons yang konsisten:

*   **GET `/api/v1/home`**
    *   Mengembalikan data untuk halaman utama (anime terbaru, movie, top 10, jadwal rilis).
    *   **Contoh Struktur JSON (Sukses):**
        ```json
        {
          "confidence_score": 1.0,
          "top10": [
            {
              "judul": "One Piece",
              "url": "https://v1.samehadaku.how/anime/one-piece/",
              "anime_slug": "one-piece",
              "rating": "8.73",
              "cover": "https://v1.samehadaku.how/wp-content/uploads/2020/04/E5RxYkWX0AAwdGH.png.jpg",
              "genres": ["Anime"]
            }
            // ... item top10 lainnya
          ],
          "new_eps": [
            {
              "judul": "Zutaboro Reijou wa Ane no Moto",
              "url": "https://v1.samehadaku.how/anime/zutaboro-reijou-wa-ane-no-moto/",
              "anime_slug": "zutaboro-reijou-wa-ane-no-moto",
              "episode": "5",
              "rilis": "5 hours yang lalu",
              "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/08/Zutaboro-Reijou-wa-Ane-no-Moto-Episode-5.jpg"
            }
            // ... item new_eps lainnya
          ],
          "movies": [
            {
              "judul": "Sidonia no Kishi Ai Tsumugu Hoshi",
              "url": "https://v1.samehadaku.how/anime/sidonia-no-kishi-ai-tsumugu-hoshi/",
              "anime_slug": "sidonia-no-kishi-ai-tsumugu-hoshi",
              "tanggal": "Jun 4, 2021",
              "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/07/108354.jpg",
              "genres": ["Action", "Sci-Fi"]
            }
            // ... item movies lainnya
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
              // ... item jadwal_rilis Monday lainnya
            ],
            "Tuesday": [
              // ... item jadwal_rilis Tuesday lainnya
            ],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": []
          }
        }
        ```
*   **GET `/api/v1/anime-terbaru?page=<int>`**
    *   Mengembalikan daftar anime terbaru.
    *   **Contoh Struktur JSON (Sukses):**
        ```json
        {
          "confidence_score": 1.0,
          "data": [
            {
              "judul": "Zutaboro Reijou wa Ane no Moto",
              "url": "https://v1.samehadaku.how/anime/zutaboro-reijou-wa-ane-no-moto/",
              "anime_slug": "zutaboro-reijou-wa-ane-no-moto",
              "episode": "5",
              "uploader": "Urusai",
              "rilis": "5 hours yang lalu",
              "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/08/Zutaboro-Reijou-wa-Ane-no-Moto-Episode-5.jpg"
            },
            {
              "judul": "Silent Witch",
              "url": "https://v1.samehadaku.how/anime/silent-witch/",
              "anime_slug": "silent-witch",
              "episode": "5",
              "uploader": "Azuki",
              "rilis": "6 hours yang lalu",
              "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/08/image-35.jpg"
            }
            // ... item anime terbaru lainnya
          ]
        }
        ```
*   **GET `/api/v1/movie?page=<int>`**
    *   Mengembalikan daftar movie.
    *   **Contoh Struktur JSON (Sukses):**
        ```json
        {
          "confidence_score": 1.0,
          "data": [
            {
              "judul": "Sidonia no Kishi Ai Tsumugu Hoshi",
              "url": "https://v1.samehadaku.how/anime/sidonia-no-kishi-ai-tsumugu-hoshi/",
              "anime_slug": "sidonia-no-kishi-ai-tsumugu-hoshi",
              "status": "Completed",
              "skor": "7.45",
              "sinopsis": "Setelah Bumi dihancurkan oleh alien yang disebut dengan Gauna, sisa manusia yang selamat menyelamatkan diri ke luar angkasa ke...",
              "views": "477265 Views",
              "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/07/108354.jpg",
              "genres": [
                "Action",
                "Sci-Fi"
              ],
              "tanggal": "N/A"
            },
            {
              "judul": "Overlord Movie 3 Sei Oukoku hen",
              "url": "https://v1.samehadaku.how/anime/overlord-movie-3-sei-oukoku-hen/",
              "anime_slug": "overlord-movie-3-sei-oukoku-hen",
              "status": "Completed",
              "skor": "7.80",
              "sinopsis": "Kerajaan Suci telah damai bertahun-tahun tanpa perang berkat tembok kolosal yang dibangun setelah tragedi bersejarah. Mereka sangat memahami betapa...",
              "views": "427583 Views",
              "cover": "https://v1.samehadaku.how/wp-content/uploads/2025/04/144101.jpg",
              "genres": [
                "Action",
                "Adventure",
                "Fantasy"
              ],
              "tanggal": "N/A"
            }
            // ... item movie lainnya
          ]
        }
        ```
*   **GET `/api/v1/jadwal-rilis`**
    *   Mengembalikan jadwal rilis untuk semua hari.
    *   **Contoh Struktur JSON (Sukses):**
        ```json
        {
          "confidence_score": 1.0,
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
            // ... item jadwal_rilis Monday lainnya
          ],
          "Tuesday": [
            {
              "title": "Sakamoto Days Cour 2",
              "url": "https://v1.samehadaku.how/anime/sakamoto-days-cour-2/",
              "anime_slug": "sakamoto-days-cour-2",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/bx184237-OJAksU2fsIPx.jpg",
              "type": "TV",
              "score": "7.9",
              "genres": ["Action", "Adult Cast"],
              "release_time": "N/A"
            },
            {
              "title": "Yuusha Party o Tsuihou Sareta Shiro Madoushi",
              "url": "https://v1.samehadaku.how/anime/yuusha-party-o-tsuihou-sareta-shiro-madoushi/",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/149889.jpg",
              "type": "TV",
              "score": "6.6",
              "genres": ["Adventure", "Fantasy"],
              "release_time": "00:30"
            },
            {
              "title": "Summer Pockets",
              "url": "https://v1.samehadaku.how/anime/summer-pockets/",
              "anime_slug": "summer-pockets",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/04/148602.jpg",
              "type": "TV",
              "score": "7.29",
              "genres": ["Slice of Life"],
              "release_time": "01:00"
            },
            {
              "title": "Kijin Gentoushou",
              "url": "https://v1.samehadaku.how/anime/kijin-gentoushou/",
              "anime_slug": "kijin-gentoushou",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/03/142919.jpg",
              "type": "TV",
              "score": "7.41",
              "genres": ["Action", "Adventure"],
              "release_time": "01:00"
            },
            {
              "title": "Grand Blue Season 2",
              "url": "https://v1.samehadaku.how/anime/grand-blue-season-2/",
              "anime_slug": "grand-blue-season-2",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/150583.jpg",
              "type": "TV",
              "score": "7.47",
              "genres": ["Comedy"],
              "release_time": "01:30"
            },
            {
              "title": "Kanojo Okarishimasu Season 4",
              "url": "https://v1.samehadaku.how/anime/kanojo-okarishimasu-season-4/",
              "anime_slug": "kanojo-okarishimasu-season-4",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/150808.jpg",
              "type": "TV",
              "score": "N/A",
              "genres": ["Comedy", "Romance"],
              "release_time": "23:30"
            }
          ],
          "Wednesday": [
            {
              "title": "Jigoku Sensei Nube (2025)",
              "url": "https://v1.samehadaku.how/anime/jigoku-sensei-nube-2025/",
              "anime_slug": "jigoku-sensei-nube-2025",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/bx179678-1isykDVghv8Q.png",
              "type": "TV",
              "score": "N/A",
              "genres": ["Comedy", "Horror"],
              "release_time": "N/A"
            },
            {
              "title": "Necronomico",
              "url": "https://v1.samehadaku.how/anime/necronomico/",
              "anime_slug": "necronomico",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/bx185505-l2ZcSDvdzhd8.jpg",
              "type": "TV",
              "score": "5.5",
              "genres": ["Video Game"],
              "release_time": "00:00"
            },
            {
              "title": "Tate no Yuusha no Nariagari Season 4",
              "url": "https://v1.samehadaku.how/anime/tate-no-yuusha-no-nariagari-season-4/",
              "anime_slug": "tate-no-yuusha-no-nariagari-season-4",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Tate-no-Yuusha-no-Nariagari-Season-4.jpg",
              "type": "TV",
              "score": "7.46",
              "genres": ["Action", "Adventure"],
              "release_time": "21:00"
            },
            {
              "title": "Clevatess",
              "url": "https://v1.samehadaku.how/anime/clevatess/",
              "anime_slug": "clevatess",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Clevatess.jpg",
              "type": "TV",
              "score": "7.91",
              "genres": ["Action", "Fantasy"],
              "release_time": "21:30"
            }
          ],
          "Thursday": [
            {
              "title": "Jidou Hanbaiki ni Umarekawatta Season 2",
              "url": "https://v1.samehadaku.how/anime/jidou-hanbaiki-ni-umarekawatta-season-2/",
              "anime_slug": "jidou-hanbaiki-ni-umarekawatta-season-2",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/150516.jpg",
              "type": "TV",
              "score": "6.60",
              "genres": ["Comedy", "Fantasy"],
              "release_time": "00:00"
            },
            {
              "title": "Tensei shitara Dainana Ouji Season 2",
              "url": "https://v1.samehadaku.how/anime/tensei-shitara-dainana-ouji-season-2/",
              "anime_slug": "tensei-shitara-dainana-ouji-season-2",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Tensei-shitara-Dainana-Ouji-Season-2.jpg",
              "type": "TV",
              "score": "7.63",
              "genres": ["Adventure", "Fantasy"],
              "release_time": "00:30"
            },
            {
              "title": "Tsuyokute New Saga",
              "url": "https://v1.samehadaku.how/anime/tsuyokute-new-saga/",
              "anime_slug": "tsuyokute-new-saga",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/147753.jpg",
              "type": "TV",
              "score": "N/A",
              "genres": ["Adventure", "Fantasy"],
              "release_time": "03:00"
            },
            {
              "title": "Uchuujin MuuMuu",
              "url": "https://v1.samehadaku.how/anime/uchuujin-muumuu/",
              "anime_slug": "uchuujin-muumuu",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/04/bx185070-VKzUA4B9kmaX.jpg",
              "type": "TV",
              "score": "6.29",
              "genres": ["Comedy", "Sci-Fi"],
              "release_time": "03:20"
            },
            {
              "title": "Onmyou Kaiten ReBirth",
              "url": "https://v1.samehadaku.how/anime/onmyou-kaiten-rebirth/",
              "anime_slug": "onmyou-kaiten-rebirth",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Onmyou-Kaiten-ReBirth.jpg",
              "type": "TV",
              "score": "6.51",
              "genres": ["Action", "Fantasy"],
              "release_time": "03:25"
            },
            {
              "title": "Dr. Stone Season 4 Part 2",
              "url": "https://v1.samehadaku.how/anime/dr-stone-season-4-part-2/",
              "anime_slug": "dr-stone-season-4-part-2",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Dr.-Stone-Season-4-Part-2.jpg",
              "type": "TV",
              "score": "8.23",
              "genres": ["Adventure", "Comedy"],
              "release_time": "22:30"
            }
          ],
          "Friday": [
            {
              "title": "Dandadan Season 2",
              "url": "https://v1.samehadaku.how/anime/dandadan-season-2/",
              "anime_slug": "dandadan-season-2",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/149001.jpg",
              "type": "TV",
              "score": "8.48",
              "genres": ["Action", "Comedy"],
              "release_time": "00:00"
            },
            {
              "title": "Mizu Zokusei no Mahoutsukai",
              "url": "https://v1.samehadaku.how/anime/mizu-zokusei-no-mahoutsukai/",
              "anime_slug": "mizu-zokusei-no-mahoutsukai",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Mizu-Zokusei-no-Mahoutsukai.jpg",
              "type": "TV",
              "score": "7.24",
              "genres": ["Action", "Fantasy"],
              "release_time": "04:00"
            }
          ],
          "Saturday": [
            {
              "title": "Tougen Anki",
              "url": "https://v1.samehadaku.how/anime/tougen-anki/",
              "anime_slug": "tougen-anki",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Tougen-Anki.jpg",
              "type": "TV",
              "score": "7.20",
              "genres": ["Action", "Fantasy"],
              "release_time": "N/A"
            },
            {
              "title": "Yofukashi no Uta Season 2",
              "url": "https://v1.samehadaku.how/anime/yofukashi-no-uta-season-2/",
              "anime_slug": "yofukashi-no-uta-season-2",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Yofukashi-no-Uta-Season-2.jpg",
              "type": "TV",
              "score": "8.25",
              "genres": ["Romance", "Shounen"],
              "release_time": "01:30"
            },
            {
              "title": "Silent Witch",
              "url": "https://v1.samehadaku.how/anime/silent-witch/",
              "anime_slug": "silent-witch",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/bx179966-g0EU7rVe2Og7.jpg",
              "type": "TV",
              "score": "7.83",
              "genres": ["Fantasy", "School"],
              "release_time": "02:30"
            },
            {
              "title": "Zutaboro Reijou wa Ane no Moto",
              "url": "https://v1.samehadaku.how/anime/zutaboro-reijou-wa-ane-no-moto/",
              "anime_slug": "zutaboro-reijou-wa-ane-no-moto",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Zutaboro-Reijou-wa-Ane-no-Moto.jpg",
              "type": "TV",
              "score": "7.21",
              "genres": ["Comedy", "Josei"],
              "release_time": "03:30"
            },
            {
              "title": "Kaijuu 8-gou Season 2",
              "url": "https://v1.samehadaku.how/anime/kaijuu-8-gou-season-2/",
              "anime_slug": "kaijuu-8-gou-season-2",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/150344.jpg",
              "type": "TV",
              "score": "7.9",
              "genres": ["Action", "Adult Cast"],
              "release_time": "23:31"
            }
          ],
          "Sunday": [
            {
              "title": "Sono Bisque Doll wa Koi wo Suru Season 2",
              "url": "https://v1.samehadaku.how/anime/sono-bisque-doll-wa-koi-wo-suru-season-2/",
              "anime_slug": "sono-bisque-doll-wa-koi-wo-suru-season-2",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/150787.jpg",
              "type": "TV",
              "score": "8.46",
              "genres": ["Romance", "School"],
              "release_time": "N/A"
            },
            {
              "title": "Isekai Mokushiroku Mynoghra",
              "url": "https://v1.samehadaku.how/anime/isekai-mokushiroku-mynoghra/",
              "anime_slug": "isekai-mokushiroku-mynoghra",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/150383.jpg",
              "type": "TV",
              "score": "7.13",
              "genres": ["Adventure", "Fantasy"],
              "release_time": "N/A"
            },
            {
              "title": "Koujo Denka no Kateikyoushi",
              "url": "https://v1.samehadaku.how/anime/koujo-denka-no-kateikyoushi/",
              "anime_slug": "koujo-denka-no-kateikyoushi",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/06/bx170113-dk9h9ybZnGnZ.jpg",
              "type": "TV",
              "score": "6.94",
              "genres": ["Fantasy"],
              "release_time": "N/A"
            },
            {
              "title": "Kizetsu Yuusha to Ansatsu Hime",
              "url": "https://v1.samehadaku.how/anime/kizetsu-yuusha-to-ansatsu-hime/",
              "anime_slug": "kizetsu-yuusha-to-ansatsu-hime",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Kizetsu-Yuusha-to-Ansatsu-Hime.jpg",
              "type": "TV",
              "score": "6.42",
              "genres": ["Action", "Comedy"],
              "release_time": "00:01"
            },
            {
              "title": "Seishun Buta Yarou wa Santa Claus no Yume wo Minai",
              "url": "https://v1.samehadaku.how/anime/seishun-buta-yarou-wa-santa-claus-no-yume-wo-minai/",
              "anime_slug": "seishun-buta-yarou-wa-santa-claus-no-yume-wo-minai",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Seishun-Buta-Yarou-wa-Santa-Claus-no-Yume-wo-Minai.jpg",
              "type": "TV",
              "score": "8.38",
              "genres": ["Drama", "Romance"],
              "release_time": "02:00"
            },
            {
              "title": "Kaoru Hana wa Rin to Saku",
              "url": "https://v1.samehadaku.how/anime/kaoru-hana-wa-rin-to-saku/",
              "anime_slug": "kaoru-hana-wa-rin-to-saku",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/Kaoru-Hana-wa-Rin-to-Saku.jpg",
              "type": "TV",
              "score": "8.78",
              "genres": ["Drama", "Romance"],
              "release_time": "03:00"
            },
            {
              "title": "Hikaru ga Shinda Natsu",
              "url": "https://v1.samehadaku.how/anime/hikaru-ga-shinda-natsu/",
              "anime_slug": "hikaru-ga-shinda-natsu",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/148614.jpg",
              "type": "TV",
              "score": "8.2",
              "genres": ["Horror", "Mystery"],
              "release_time": "03:00"
            },
            {
              "title": "Witch Watch",
              "url": "https://v1.samehadaku.how/anime/witch-watch/",
              "anime_slug": "witch-watch",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/04/148017.jpg",
              "type": "TV",
              "score": "6.2",
              "genres": ["Comedy", "Supernatural"],
              "release_time": "18:30"
            },
            {
              "title": "Gachiakuta",
              "url": "https://v1.samehadaku.how/anime/gachiakuta/",
              "anime_slug": "gachiakuta",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/150432.jpg",
              "type": "TV",
              "score": "8.08",
              "genres": ["Action", "Fantasy"],
              "release_time": "23:59"
            }
          ]
        }
        ```
*   **GET `/api/v1/jadwal-rilis/<day>`** (e.g., `/api/v1/jadwal-rilis/monday`)
    *   Mengembalikan jadwal rilis untuk hari tertentu.
    *   **Contoh Struktur JSON (Sukses):**
        ```json
        {
          "confidence_score": 1.0,
          "data": [
            {
              "title": "Busamen Gachi Fighter",
              "url": "https://v1.samehadaku.how/anime/busamen-gachi-fighter/",
              "anime_slug": "busamen-gachi-fighter",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2025/07/150515.jpg",
              "type": "TV",
              "score": "6.68",
              "genres": [
                "Action",
                "Adventure"
              ],
              "release_time": "00:00"
            }
            // ... item jadwal hari ini lainnya
          ]
        }
        ```
*   **GET `/api/v1/anime-detail?anime_slug=<string>`**
    *   Mengembalikan detail lengkap untuk anime tertentu.
    *   **Contoh Struktur JSON (Sukses):**
        ```json
        {
          "confidence_score": 1.0,
          "judul": "Nonton Anime Boku no Hero Academia the Movie 4",
          "url_anime": "https://v1.samehadaku.how/anime/boku-no-hero-academia-the-movie-4/",
          "anime_slug": "boku-no-hero-academia-the-movie-4",
          "url_cover": "https://v1.samehadaku.how/wp-content/uploads/2025/02/143549.jpg",
          "episode_list": [
            {
              "episode": "1",
              "title": "Boku no Hero Academia the Movie 4 You’re Next",
              "url": "https://v1.samehadaku.how/boku-no-hero-academia-the-movie-youre-next/",
              "episode_slug": "boku-no-hero-academia-the-movie-youre-next",
              "release_date": "22 February 2025"
            }
          ],
          "recommendations": [
            {
              "title": "Re:Zero kara Hajimeru Isekai Seikatsu Season 2",
              "url": "https://v1.samehadaku.how/anime/rezero-kara-hajimeru-isekai-seikatsu-season-2/",
              "anime_slug": "rezero-kara-hajimeru-isekai-seikatsu-season-2",
              "cover_url": "https://v1.samehadaku.how/wp-content/uploads/2020/07/108005.jpg",
              "rating": "8.79",
              "episode": "Eps 13"
            }
          ],
          "status": "Completed",
          "tipe": "Movie",
          "skor": "7.5",
          "penonton": "N/A",
          "sinopsis": "Movie ke 4 dari Boku no Hero Academia",
          "genre": [
            "Action",
            "School",
            "Super Power"
          ],
          "details": {
            "Japanese": "僕のヒーローアカデミアTHE MOVIE ユアネクスト",
            "English": "My Hero Academia: You're Next",
            "Status": "Completed",
            "Type": "Movie",
            "Source": "Manga",
            "Duration": "1 hr. 50 min.",
            "Total Episode": "1",
            "Season": "Movie",
            "Studio": "Bones",
            "Producers": "Dentsu, Movic, Nippon Television Network, Shueisha, Sony Music Entertainment, Toho, TOHO animation, Yomiuri Telecasting",
            "Released:": "Aug 2, 2024"
          },
          "rating": {
            "score": "7.5",
            "users": "7,820"
          }
        }
        ```
*   **GET `/api/v1/episode-detail?episode_url=<string>`**
    *   Mengembalikan detail lengkap untuk episode tertentu (termasuk link video dan download).
    *   **Contoh Struktur JSON (Sukses):**
        ```json
        {
          "confidence_score": 1.0,
          "title": "Boku no Hero Academia the Movie 4 You’re Next Sub Indo",
          "thumbnail_url": "https://v1.samehadaku.how/wp-content/uploads/2025/02/143549.jpg",
          "streaming_servers": [
            {
              "server_name": "Nakama 1080p",
              "streaming_url": "https://pixeldrain.com/api/file/7oKMEmKt"
            },
            {
              "server_name": "Nakama 360p",
              "streaming_url": "https://pixeldrain.com/api/file/SiFZpBKR"
            }
            // ... server streaming lainnya
          ],
          "release_info": "5 months yang lalu",
          "download_links": {
            "MKV": {
              "360p": [
                {
                  "provider": "Gofile",
                  "url": "https://gofile.io/d/6gNJq6"
                }
                // ... link download 360p MKV lainnya
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
            },
            "x265 [Mode Irit Kuota tapi Kualitas Sama Beningnya]": {
              "480p": [],
              "720p": [],
              "1080p": []
            }
          },
          "navigation": {
            "previous_episode_url": "#",
            "all_episodes_url": "https://v1.samehadaku.how/anime/boku-no-hero-academia-the-movie-4/",
            "next_episode_url": null
          },
          "anime_info": {
            "title": "Boku no Hero Academia the Movie 4",
            "thumbnail_url": "https://v1.samehadaku.how/wp-content/uploads/2025/02/143549.jpg",
            "synopsis": "Movie ke 4 dariBoku no Hero AcademiaTonton juga",
            "genres": [
              "Action",
              "School",
              "Super Power"
            ]
          },
          "other_episodes": [
            {
              "title": "Boku no Hero Academia the Movie 4 You’re Next",
              "url": "https://v1.samehadaku.how/boku-no-hero-academia-the-movie-youre-next/",
              "thumbnail_url": "https://v1.samehadaku.how/wp-content/uploads/2025/02/bOKU-hero-movie-4.jpg",
              "release_date": "22 February 2025"
            }
            // ... episode lain dari anime yang sama
          ]
        }
        ```
*   **GET `/api/v1/search?query=<string>`**
    *   Mengembalikan hasil pencarian anime.
    *   **Contoh Struktur JSON (Sukses):**
        ```json
        {
          "confidence_score": 1.0,
          "data": [
            {
              "judul": "Naruto Kecil",
              "url_anime": "https://v1.samehadaku.how/anime/naruto-kecil/",
              "anime_slug": "naruto-kecil",
              "status": "Completed",
              "tipe": "TV",
              "skor": "8.84",
              "penonton": "154157 Views",
              "sinopsis": "Beberapa saat sebelum Naruto Uzumaki lahir, seekor iblis besar yang dikenal sebagai Rubah Ekor Sembilan menyerang Konohagakure, Desa Daun...",
              "genre": [
                "Action",
                "Adventure",
                "Fantasy",
                "Martial Arts",
                "Shounen"
              ],
              "url_cover": "https://v1.samehadaku.how/wp-content/uploads/2024/08/142503.jpg"
            },
            {
              "judul": "Boruto: Naruto Next Generations",
              "url_anime": "https://v1.samehadaku.how/anime/boruto-naruto-next-generations/",
              "anime_slug": "boruto-naruto-next-generations",
              "status": "Completed",
              "tipe": "TV",
              "skor": "6.06",
              "penonton": "549360 Views",
              "sinopsis": "Sinopsis anime Boruto: Naruto Next Generations : Setelah suksesnya Perang Dunia Shinobi Keempat, Konohagakure telah menikmati masa damai, kemakmuran,...",
              "genre": [
                "Action",
                "Adventure",
                "Fantasy",
                "Martial Arts",
                "Shounen"
              ],
              "url_cover": "https://v1.samehadaku.how/wp-content/uploads/2021/12/poster-boruto.jpg"
            }
            // ... hasil pencarian lainnya
          ]
        }
        ```
*   **GET `/health`**
    *   Endpoint health check.
    *   **Contoh Struktur JSON (Sukses):**
        ```json
        {
          "status": "ok"
        }
        ```
    *   **Contoh Struktur JSON (Gagal):**
        ```json
        {
          "status": "error",
          "message": "Database connection failed"
        }
        ```


## 6. Deployment

*   Pertimbangkan untuk menggunakan Docker untuk mengemas aplikasi API Anda. Ini akan menyederhanakan deployment dan memastikan konsistensi lingkungan.
*   Untuk skala, Anda dapat menjalankan beberapa instance API scraping ini di belakang load balancer.

## 7. Alur Kerja Integrasi API dan Django

Berikut adalah visualisasi alur kerja bagaimana aplikasi Django KortekStream berinteraksi dengan API web scraping Anda:

```mermaid
graph TD
    A[Pengguna Mengakses Halaman Django] --> B{Django Membutuhkan Data}
    B --> C{Panggil API Client Django}
    C --> D[API Client Django]
    D --> E{Pilih API Endpoint (Berdasarkan Prioritas)}
    E --> F{Kirim Permintaan HTTP ke API Scraping}
    F --> G[API Web Scraping Anda]
    G --> H{Lakukan Web Scraping dari Situs Sumber}
    H --> I{Proses & Standardisasi Data}
    I --> J{Hitung Confidence Score}
    J --> K{Kembalikan Respons JSON ke Django}
    K --> L[API Client Django Menerima Respons]
    L --> M{Periksa Confidence Score}
    M -- Confidence Rendah --> E
    M -- Confidence Tinggi --> N[Django Mengolah Data]
    N --> O[Tampilkan Data di Halaman Django]
    O --> P[Pengguna Melihat Data]

    subgraph Fallback & Monitoring
        E -- Gagal/Timeout --> E
        E -- Gagal/Timeout --> Q[Catat di APIMonitor]
        Q --> R[Dashboard Monitoring API]
        R --> S[Celery Task: check_api_status]
        S --> E
    end

    subgraph Caching
        D -- Cache Hit --> N
        N -- Cache Miss --> E
        K -- Cacheable Data --> T[Cache Data di Django]
    end
```

### Bagaimana Mengembangkan API Web Scraping Anda

1.  **Pilih Teknologi:** Putuskan apakah Anda akan menggunakan Go, FastAPI, atau teknologi lain. Pertimbangkan performa, kecepatan pengembangan, dan ekosistem pustaka yang tersedia.
2.  **Desain Struktur Data:** Ini adalah langkah paling krusial. Ikuti dengan cermat struktur JSON yang diharapkan oleh Django untuk setiap endpoint (seperti yang dijelaskan di Bagian 5). Pastikan semua field yang diperlukan ada dan tipe datanya sesuai.
3.  **Implementasikan Logika Scraping:** Untuk setiap endpoint, tulis kode untuk:
    *   Mengirim permintaan HTTP ke situs sumber (gunakan `requests` di Python, `net/http` di Go).
    *   Parse HTML yang diterima (gunakan `BeautifulSoup4`/`lxml` di Python, `goquery`/`colly` di Go).
    *   Ekstrak data yang relevan dan transformasikan ke struktur JSON yang diharapkan.
    *   Tangani anti-bot measures (User-Agent, delay, proxy) untuk menghindari pemblokiran.
    *   Gunakan headless browser jika situs sumber merender konten dengan JavaScript.
4.  **Hitung `confidence_score`:** Kembangkan logika untuk menilai kualitas data yang di-scrape. Misalnya:
    *   Jika semua field penting berhasil di-scrape: `1.0`
    *   Jika ada beberapa field yang hilang atau tidak valid: `0.5 - 0.9` (sesuai tingkat keparahan)
    *   Jika scraping gagal total atau data sangat tidak lengkap: `0.0`
5.  **Implementasikan Penanganan Kesalahan:** Pastikan API Anda mengembalikan kode status HTTP yang benar dan pesan kesalahan yang informatif dalam format JSON yang ditentukan.
6.  **Buat Endpoint Health Check:** Sediakan endpoint `/health` yang sederhana untuk memungkinkan Django memverifikasi ketersediaan API Anda.
7.  **Uji Secara Menyeluruh:** Uji setiap endpoint API Anda dengan berbagai skenario (sukses, gagal, data tidak ditemukan, dll.) untuk memastikan konsistensi dan keandalan.
8.  **Deploy API Anda:** Gunakan Docker untuk mengemas dan mendeploy API Anda. Pastikan API dapat diakses oleh aplikasi Django (misalnya, di `http://localhost:8001` atau URL publik).

### Bagaimana Django Mengolah Data dari API Anda

Aplikasi Django KortekStream dirancang untuk menjadi klien cerdas dari API web scraping Anda. Berikut adalah cara kerjanya:

1.  **`APIEndpoint` Model:** Django menyimpan daftar API yang tersedia di database melalui model `APIEndpoint`. Setiap entri memiliki URL, prioritas, dan status aktif.
2.  **`FallbackAPIClient`:** Ini adalah inti dari logika konsumsi API di Django (`streamapp/api_client.py`).
    *   Ketika Django membutuhkan data (misalnya, untuk halaman beranda atau detail anime), `FallbackAPIClient` akan memilih API dengan prioritas tertinggi yang aktif.
    *   Ia akan mengirim permintaan HTTP ke API tersebut.
    *   Jika respons sukses diterima, `FallbackAPIClient` akan memeriksa `confidence_score`.
    *   **Fallback Otomatis:**
        *   Jika `confidence_score` terlalu rendah (di bawah ambang batas yang ditentukan, saat ini 0.5), atau jika permintaan HTTP gagal (timeout, connection refused, HTTP error), `FallbackAPIClient` akan secara otomatis mencoba API berikutnya dalam daftar prioritas.
        *   Proses ini berlanjut hingga data yang valid dengan `confidence_score` yang memadai ditemukan, atau hingga semua API habis dicoba.
    *   **Pembaruan `APIMonitor`:** Setiap interaksi dengan API (sukses atau gagal) akan dicatat ke model `APIMonitor` di database Django. Ini digunakan untuk dashboard monitoring API Anda.
    *   **Pembaruan `APIEndpoint`:** Saat API berhasil digunakan, `last_used` dan `success_count` pada model `APIEndpoint` yang bersangkutan akan diperbarui.
3.  **Caching di Django:** Django juga mengimplementasikan caching di sisi server (menggunakan `django.core.cache`) untuk respons API. Ini berarti jika data yang sama diminta berulang kali, Django akan melayani dari cache daripada memanggil API scraping lagi, mengurangi beban pada API Anda dan situs sumber.
4.  **Transformasi Data (Opsional):** Beberapa view di Django mungkin melakukan sedikit transformasi pada data yang diterima dari API agar sesuai dengan struktur yang diharapkan oleh template. Namun, semakin konsisten API Anda, semakin sedikit transformasi yang diperlukan di sisi Django.
5.  **Tampilan Data:** Setelah data berhasil diambil dan diolah, Django akan meneruskannya ke template HTML yang sesuai untuk dirender dan ditampilkan kepada pengguna.

Dengan alur kerja ini, aplikasi Django Anda menjadi sangat tangguh terhadap kegagalan atau kualitas data yang buruk dari satu sumber API scraping, karena ia dapat secara cerdas beralih ke sumber lain untuk memastikan pengalaman pengguna yang lancar.
