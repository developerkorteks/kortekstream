#!/usr/bin/env python
"""
Server FastAPI dummy untuk pengujian fallback API.
"""
import sys
import uvicorn
from fastapi import FastAPI, Query
from typing import List, Dict, Any, Optional
import random

app = FastAPI(title="Dummy API Server")

# Data dummy
ANIME_TERBARU = [
    {
        "title": "Anime Test 1",
        "episode": "Episode 1",
        "url": "/episode/anime-test-1-episode-1/",
        "thumbnail_url": "https://example.com/thumbnail1.jpg",
        "upload_time": "2 jam lalu"
    },
    {
        "title": "Anime Test 2",
        "episode": "Episode 5",
        "url": "/episode/anime-test-2-episode-5/",
        "thumbnail_url": "https://example.com/thumbnail2.jpg",
        "upload_time": "5 jam lalu"
    }
]

MOVIE_LIST = [
    {
        "title": "Movie Test 1",
        "url": "/anime/movie-test-1/",
        "thumbnail_url": "https://example.com/movie1.jpg",
        "score": "8.5"
    },
    {
        "title": "Movie Test 2",
        "url": "/anime/movie-test-2/",
        "thumbnail_url": "https://example.com/movie2.jpg",
        "score": "9.0"
    }
]

TOP10_ANIME = [
    {
        "title": "Top Anime 1",
        "url": "/anime/top-anime-1/",
        "thumbnail_url": "https://example.com/top1.jpg",
        "score": "9.5"
    },
    {
        "title": "Top Anime 2",
        "url": "/anime/top-anime-2/",
        "thumbnail_url": "https://example.com/top2.jpg",
        "score": "9.2"
    }
]

JADWAL_RILIS = {
    "monday": [
        {
            "title": "Monday Anime 1",
            "url": "/anime/monday-anime-1/",
            "thumbnail_url": "https://example.com/monday1.jpg"
        }
    ],
    "tuesday": [
        {
            "title": "Tuesday Anime 1",
            "url": "/anime/tuesday-anime-1/",
            "thumbnail_url": "https://example.com/tuesday1.jpg"
        }
    ]
}

@app.get("/health")
def health_check():
    """
    Endpoint untuk health check.
    """
    return {"status": "ok", "server_id": sys.argv[1] if len(sys.argv) > 1 else "unknown"}

@app.get("/home")
def get_home(confidence: float = Query(1.0, ge=0.0, le=1.0)):
    """
    Endpoint untuk halaman utama.
    
    Args:
        confidence: Confidence score untuk pengujian validasi
    """
    return {
        "confidence_score": confidence,
        "data": {
            "top10": TOP10_ANIME,
            "new_eps": ANIME_TERBARU,
            "movies": MOVIE_LIST,
            "jadwal_rilis": JADWAL_RILIS
        }
    }

@app.get("/api/v1/home/")
def get_home_v1(confidence: float = Query(1.0, ge=0.0, le=1.0), force_refresh: bool = Query(False)):
    """
    Endpoint untuk halaman utama (API v1).
    
    Args:
        confidence: Confidence score untuk pengujian validasi
        force_refresh: Force refresh cache
    """
    return {
        "confidence_score": confidence,
        "data": {
            "top10": TOP10_ANIME,
            "new_eps": ANIME_TERBARU,
            "movies": MOVIE_LIST,
            "jadwal_rilis": JADWAL_RILIS
        }
    }

@app.get("/anime-terbaru")
def get_anime_terbaru(page: int = Query(1, ge=1), confidence: float = Query(1.0, ge=0.0, le=1.0)):
    """
    Endpoint untuk anime terbaru.
    
    Args:
        page: Nomor halaman
        confidence: Confidence score untuk pengujian validasi
    """
    return {
        "confidence_score": confidence,
        "data": ANIME_TERBARU
    }

@app.get("/movie")
def get_movie(page: int = Query(1, ge=1), confidence: float = Query(1.0, ge=0.0, le=1.0)):
    """
    Endpoint untuk movie.
    
    Args:
        page: Nomor halaman
        confidence: Confidence score untuk pengujian validasi
    """
    return {
        "confidence_score": confidence,
        "data": MOVIE_LIST
    }

@app.get("/api/v1/movie/")
def get_movie_v1(page: int = Query(1, ge=1), confidence: float = Query(1.0, ge=0.0, le=1.0), force_refresh: bool = Query(False)):
    """
    Endpoint untuk movie (API v1).
    
    Args:
        page: Nomor halaman
        confidence: Confidence score untuk pengujian validasi
        force_refresh: Force refresh cache
    """
    return {
        "confidence_score": confidence,
        "data": MOVIE_LIST
    }

@app.get("/jadwal-rilis")
def get_jadwal_rilis(confidence: float = Query(1.0, ge=0.0, le=1.0)):
    """
    Endpoint untuk jadwal rilis.
    
    Args:
        confidence: Confidence score untuk pengujian validasi
    """
    return {
        "confidence_score": confidence,
        "data": JADWAL_RILIS
    }

@app.get("/jadwal-rilis/{day}")
def get_jadwal_rilis_day(day: str, confidence: float = Query(1.0, ge=0.0, le=1.0)):
    """
    Endpoint untuk jadwal rilis berdasarkan hari.
    
    Args:
        day: Hari dalam seminggu
        confidence: Confidence score untuk pengujian validasi
    """
    return {
        "confidence_score": confidence,
        "data": JADWAL_RILIS.get(day.lower(), [])
    }

@app.get("/anime-detail")
def get_anime_detail(anime_slug: str, confidence: float = Query(1.0, ge=0.0, le=1.0)):
    """
    Endpoint untuk detail anime.
    
    Args:
        anime_slug: Slug anime
        confidence: Confidence score untuk pengujian validasi
    """
    return {
        "confidence_score": confidence,
        "data": {
            "title": f"Anime {anime_slug}",
            "thumbnail_url": "https://example.com/anime.jpg",
            "url_cover": "https://example.com/cover.jpg",
            "sinopsis": "Ini adalah sinopsis anime.",
            "genres": ["Action", "Adventure"],
            "details": {"Status": "Ongoing"},
            "episode_list": [
                {
                    "episode": "Episode 1",
                    "url": f"/episode/{anime_slug}-episode-1/",
                    "upload_time": "2 hari lalu"
                }
            ]
        }
    }

@app.get("/episode-detail")
def get_episode_detail(episode_url: str, confidence: float = Query(1.0, ge=0.0, le=1.0)):
    """
    Endpoint untuk detail episode.
    
    Args:
        episode_url: URL episode
        confidence: Confidence score untuk pengujian validasi
    """
    return {
        "confidence_score": confidence,
        "data": {
            "title": f"Episode dari {episode_url}",
            "anime_info": {
                "title": "Anime Test",
                "url": "/anime/anime-test/"
            },
            "video_urls": [
                {
                    "quality": "720p",
                    "url": "https://example.com/video.mp4"
                }
            ],
            "navigation": {
                "prev_episode": None,
                "next_episode": None,
                "all_episodes_url": "/anime/anime-test/"
            },
            "other_episodes": []
        }
    }

@app.get("/search")
def search_anime(query: str, confidence: float = Query(1.0, ge=0.0, le=1.0)):
    """
    Endpoint untuk pencarian anime.
    
    Args:
        query: Query pencarian
        confidence: Confidence score untuk pengujian validasi
    """
    return {
        "confidence_score": confidence,
        "data": [
            {
                "title": f"Result for {query} 1",
                "url_anime": f"/anime/result-{query}-1/",
                "thumbnail_url": "https://example.com/result1.jpg"
            },
            {
                "title": f"Result for {query} 2",
                "url_anime": f"/anime/result-{query}-2/",
                "thumbnail_url": "https://example.com/result2.jpg"
            }
        ]
    }

if __name__ == "__main__":
    # Ambil port dari argumen command line
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    # Jalankan server
    uvicorn.run(app, host="0.0.0.0", port=port)