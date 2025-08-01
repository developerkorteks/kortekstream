import random
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional, List, Dict, Any, Union
import time

app = FastAPI(title="Dummy Broken API Server")

# Tambahkan CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Jenis-jenis respons yang rusak
BROKEN_RESPONSES = [
    None,  # Respons kosong
    {},  # Objek kosong
    [],  # Array kosong
    {"error": "Internal server error"},  # Error
    {"data": None},  # Data kosong
    {"data": []},  # Data array kosong
    {"data": {}},  # Data objek kosong
    {"wrong_key": []},  # Kunci yang salah
    {"new_eps": None},  # new_eps kosong
    {"new_eps": [], "movies": None},  # movies kosong
    {"new_eps": [], "movies": [], "top10": None},  # top10 kosong
    {"new_eps": [], "movies": [], "top10": [], "jadwal_rilis": None},  # jadwal_rilis kosong
    {"new_eps": "bukan array"},  # Tipe data yang salah
    {"new_eps": [1, 2, 3]},  # Array dengan tipe data yang salah
    {"new_eps": [{"title": "Anime 1"}]},  # Array dengan struktur yang tidak lengkap
]

# Endpoint untuk halaman utama
@app.get("/home")
async def home():
    # Pilih respons yang rusak secara acak
    response_type = random.choice(BROKEN_RESPONSES)
    # Tambahkan delay untuk simulasi jaringan lambat
    time.sleep(random.uniform(0.1, 0.5))
    return response_type

# Endpoint untuk anime terbaru
@app.get("/anime-terbaru")
async def anime_terbaru(page: int = Query(1, ge=1)):
    # Pilih respons yang rusak secara acak
    response_type = random.choice(BROKEN_RESPONSES)
    # Tambahkan delay untuk simulasi jaringan lambat
    time.sleep(random.uniform(0.1, 0.5))
    return response_type

# Endpoint untuk movie
@app.get("/movie")
async def movie(page: int = Query(1, ge=1)):
    # Pilih respons yang rusak secara acak
    response_type = random.choice(BROKEN_RESPONSES)
    # Tambahkan delay untuk simulasi jaringan lambat
    time.sleep(random.uniform(0.1, 0.5))
    return response_type

# Endpoint untuk jadwal rilis
@app.get("/jadwal-rilis")
async def jadwal_rilis(day: Optional[str] = None):
    # Pilih respons yang rusak secara acak
    response_type = random.choice(BROKEN_RESPONSES)
    # Tambahkan delay untuk simulasi jaringan lambat
    time.sleep(random.uniform(0.1, 0.5))
    return response_type

# Endpoint untuk detail anime
@app.get("/anime-detail")
async def anime_detail(anime_slug: str):
    # Pilih respons yang rusak secara acak
    response_type = random.choice(BROKEN_RESPONSES)
    # Tambahkan delay untuk simulasi jaringan lambat
    time.sleep(random.uniform(0.1, 0.5))
    return response_type

# Endpoint untuk detail episode
@app.get("/episode-detail")
async def episode_detail(episode_url: str):
    # Pilih respons yang rusak secara acak
    response_type = random.choice(BROKEN_RESPONSES)
    # Tambahkan delay untuk simulasi jaringan lambat
    time.sleep(random.uniform(0.1, 0.5))
    return response_type

# Endpoint untuk pencarian
@app.get("/search")
async def search(query: str):
    # Pilih respons yang rusak secara acak
    response_type = random.choice(BROKEN_RESPONSES)
    # Tambahkan delay untuk simulasi jaringan lambat
    time.sleep(random.uniform(0.1, 0.5))
    return response_type

if __name__ == "__main__":
    print("Menjalankan server dummy API dengan respons yang rusak di http://localhost:8003")
    print("Tekan Ctrl+C untuk menghentikan server")
    uvicorn.run(app, host="0.0.0.0", port=8003)