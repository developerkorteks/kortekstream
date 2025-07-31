from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnimeBase(BaseModel):
    """Base model for anime data."""
    judul: str
    url_anime: str = Field(..., description="URL to anime page")
    anime_slug: Optional[str] = Field(None, description="Anime slug for URL")
    status: Optional[str] = None
    tipe: Optional[str] = None
    skor: Optional[str] = None
    penonton: Optional[str] = None
    sinopsis: Optional[str] = None
    genre: Optional[List[str]] = None
    url_cover: Optional[str] = None


class AnimeSearch(AnimeBase):
    """Model for anime search results."""
    pass


class AnimeEpisode(BaseModel):
    """Model for anime episode data."""
    episode: str
    title: str
    url: str
    episode_slug: Optional[str] = None
    release_date: Optional[str] = None


class AnimeDetail(AnimeBase):
    """Model for detailed anime data."""
    details: Optional[Dict[str, Any]] = None
    rating: Optional[Dict[str, Any]] = None
    episode_list: Optional[List[AnimeEpisode]] = None
    recommendations: Optional[List[Any]] = None


class EpisodeServer(BaseModel):
    """Model for episode streaming server."""
    server_name: str
    streaming_url: str


class DownloadProvider(BaseModel):
    """Model for download provider."""
    provider: str
    url: str


class EpisodeNavigation(BaseModel):
    """Model for episode navigation."""
    previous_episode_url: Optional[str] = None
    next_episode_url: Optional[str] = None
    all_episodes_url: Optional[str] = None


class EpisodeDetail(BaseModel):
    """Model for detailed episode data."""
    title: str
    release_info: Optional[str] = None
    streaming_servers: List[EpisodeServer] = []
    download_links: Dict[str, Dict[str, List[DownloadProvider]]] = {}
    navigation: EpisodeNavigation = Field(default_factory=EpisodeNavigation)
    anime_info: Dict[str, Any] = {}
    other_episodes: List[Dict[str, Any]] = []


class AnimeScheduleItem(BaseModel):
    """Model for anime schedule item."""
    title: str
    url: str
    anime_slug: Optional[str] = None
    cover_url: Optional[str] = None
    type: Optional[str] = None
    score: Optional[str] = None
    genres: Optional[List[str]] = None
    release_time: Optional[str] = None


class AnimeSchedule(BaseModel):
    """Model for anime schedule."""
    Monday: List[AnimeScheduleItem] = []
    Tuesday: List[AnimeScheduleItem] = []
    Wednesday: List[AnimeScheduleItem] = []
    Thursday: List[AnimeScheduleItem] = []
    Friday: List[AnimeScheduleItem] = []
    Saturday: List[AnimeScheduleItem] = []
    Sunday: List[AnimeScheduleItem] = []


class AnimeTerbaru(BaseModel):
    """Model for latest anime."""
    judul: str
    url: str
    anime_slug: Optional[str] = None
    episode: Optional[str] = None
    rilis: Optional[str] = None
    cover: Optional[str] = None


class AnimeMovie(BaseModel):
    """Model for anime movie."""
    judul: str
    url: str
    anime_slug: Optional[str] = None
    tanggal: Optional[str] = None
    cover: Optional[str] = None
    genres: Optional[List[str]] = None


class AnimeMingguan(BaseModel):
    """Model for weekly anime."""
    judul: str
    url: str
    anime_slug: Optional[str] = None
    rating: Optional[str] = None
    cover: Optional[str] = None
    genres: Optional[List[str]] = None


class HomeData(BaseModel):
    """Model for home page data."""
    top10: List[AnimeMingguan] = []
    new_eps: List[AnimeTerbaru] = []
    movies: List[AnimeMovie] = []
    jadwal_rilis: Optional[AnimeSchedule] = None