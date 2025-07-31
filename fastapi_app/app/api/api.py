from fastapi import APIRouter

from .endpoints import jadwal_rilis, anime_terbaru, movie, anime_detail, episode_detail, search, home

api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(home.router, prefix="/home", tags=["home"])
api_router.include_router(jadwal_rilis.router, prefix="/jadwal-rilis", tags=["jadwal-rilis"])
api_router.include_router(anime_terbaru.router, prefix="/anime-terbaru", tags=["anime-terbaru"])
api_router.include_router(movie.router, prefix="/movie", tags=["movie"])
api_router.include_router(anime_detail.router, prefix="/anime-detail", tags=["anime-detail"])
api_router.include_router(episode_detail.router, prefix="/episode-detail", tags=["episode-detail"])
api_router.include_router(search.router, prefix="/search", tags=["search"])