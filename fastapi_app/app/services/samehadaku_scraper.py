import re
import logging
import requests
from typing import Any, Dict, List, Optional, Union
from bs4 import BeautifulSoup
import concurrent.futures
import time

from .scraper import BaseScraper

logger = logging.getLogger(__name__)


class SamehadakuScraper(BaseScraper):
    """
    Scraper for Samehadaku.
    """
    def __init__(self, source_name: str = "samehadaku"):
        super().__init__(source_name)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        })
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for anime on Samehadaku.
        """
        search_url = f"{self.search_url}/?s={query}"
        logger.info(f"Searching for '{query}' at {search_url}")
        
        try:
            soup = self.get_soup(search_url)
            search_results = []
            
            # Setiap hasil pencarian ada di dalam tag <article class="animpost">
            articles = soup.select("main.relat article.animpost")
            
            if not articles:
                logger.warning(f"No results found for query '{query}'")
                return []
            
            for article in articles:
                # Mengambil elemen-elemen utama
                link_tag = article.select_one("a")
                title_tag = article.select_one(".data .title h2")
                status_tag = article.select_one(".data .type")
                type_tag = article.select_one(".content-thumb .type")  # Tipe (TV, Movie, dll.)
                score_tag = article.select_one(".content-thumb .score")  # Skor
                cover_tag = article.select_one(".content-thumb img")  # Cover Image
                
                # Mengambil data dari tooltip hover
                tooltip = article.select_one(".stooltip")
                synopsis_tag = tooltip.select_one(".ttls") if tooltip else None
                genre_tags = tooltip.select(".genres a") if tooltip else []
                
                # Ekstraksi jumlah penonton dari metadata di dalam tooltip
                views = "N/A"
                if tooltip:
                    metadata_spans = tooltip.select(".metadata span")
                    for span in metadata_spans:
                        if "Views" in span.text:
                            views = span.text.strip()
                            break
                
                # Ekstrak anime_slug dari URL
                anime_slug = None
                url = link_tag.get('href') if link_tag else "N/A"
                if url != "N/A":
                    anime_match = re.search(r'anime/([^/]+)', url)
                    if anime_match:
                        anime_slug = anime_match.group(1)
                
                search_results.append({
                    "judul": title_tag.text.strip() if title_tag else "N/A",
                    "url_anime": url,
                    "anime_slug": anime_slug,
                    "status": status_tag.text.strip() if status_tag else "N/A",
                    "tipe": type_tag.text.strip() if type_tag else "N/A",
                    "skor": score_tag.text.strip() if score_tag else "N/A",
                    "penonton": views,
                    "sinopsis": synopsis_tag.text.strip() if synopsis_tag else "N/A",
                    "genre": [tag.text.strip() for tag in genre_tags],
                    "url_cover": cover_tag.get('src') if cover_tag else "N/A"
                })
            
            return search_results
        
        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")
            return []
    
    def get_anime_details(self, anime_slug: str) -> Dict[str, Any]:
        """
        Get anime details from Samehadaku.
        """
        url = f"{self.base_url}/anime/{anime_slug}/"
        logger.info(f"Getting anime details from {url}")
        
        try:
            soup = self.get_soup(url)
            anime_details = {}
            
            # --- Informasi Utama ---
            info_box = soup.find("div", class_="infoanime")
            if not info_box:
                logger.error("Main information box not found")
                return {}
            
            anime_details['judul'] = info_box.find("h2", class_="entry-title").text.strip()
            anime_details['url_anime'] = url
            anime_details['anime_slug'] = anime_slug
            anime_details['url_cover'] = info_box.find("img")['src'] if info_box.find("img") else "N/A"
            
            synopsis_p = info_box.select_one("div.desc .entry-content p")
            anime_details['sinopsis'] = synopsis_p.text.strip() if synopsis_p else "N/A"
            
            rating_value = info_box.select_one(".archiveanime-rating span[itemprop='ratingValue']")
            rating_count = info_box.select_one(".archiveanime-rating i[itemprop='ratingCount']")
            anime_details['rating'] = {
                "score": rating_value.text.strip() if rating_value else "N/A",
                "users": rating_count.text.strip() if rating_count else "N/A"
            }
            anime_details['skor'] = rating_value.text.strip() if rating_value else "N/A"
            
            genres = info_box.select(".genre-info a")
            anime_details['genre'] = [genre.text.strip() for genre in genres]
            
            # --- Detail Teknis ---
            detail_box = soup.find("div", class_="spe")
            details_data = {}
            if detail_box:
                for span in detail_box.find_all("span", recursive=False):
                    if key_tag := span.find("b"):
                        key = key_tag.text.strip()
                        key_tag.decompose()
                        value = span.text.strip()
                        details_data[key] = value
            anime_details['details'] = details_data
            
            # Tambahkan field tipe dan status dari details_data
            if 'Type' in details_data:
                anime_details['tipe'] = details_data['Type']
            if 'Status' in details_data:
                anime_details['status'] = details_data['Status']
            
            # --- Daftar Episode ---
            episode_list = []
            if episode_container := soup.find("div", class_="lstepsiode"):
                for ep in episode_container.find_all("li"):
                    episode_title_tag = ep.select_one(".lchx a")
                    episode_num_tag = ep.select_one(".eps a")
                    episode_date_tag = ep.select_one(".date")
                    
                    # Ekstrak episode_slug dari URL
                    episode_slug = None
                    episode_url = episode_title_tag['href'] if episode_title_tag else "N/A"
                    if episode_url != "N/A":
                        episode_slug = episode_url.replace(f"{self.base_url}/", "").rstrip("/")
                    
                    episode_list.append({
                        "episode": episode_num_tag.text.strip() if episode_num_tag else "N/A",
                        "title": episode_title_tag.text.strip() if episode_title_tag else "N/A",
                        "url": episode_url,
                        "episode_slug": episode_slug,
                        "release_date": episode_date_tag.text.strip() if episode_date_tag else "N/A"
                    })
            
            # Fungsi untuk mengekstrak angka dari string episode
            def extract_episode_number(episode_str):
                try:
                    # Ekstrak angka dari string (misalnya "1031 FIX" menjadi 1031)
                    match = re.search(r'(\d+)', str(episode_str.get('episode', '0')))
                    if match:
                        return int(match.group(1))
                    return 0
                except Exception:
                    return 0
            
            # Urutkan episode berdasarkan nomor episode (ekstrak angka saja)
            anime_details['episode_list'] = sorted(episode_list, key=extract_episode_number, reverse=True)
            
            # --- Rekomendasi Anime Lainnya ---
            recommendations_list = []
            if rec_container := soup.select_one("div.rand-animesu ul"):
                for item in rec_container.select("li"):
                    link_tag = item.select_one("a.series")
                    if link_tag:
                        title_tag = link_tag.select_one("span.judul")
                        rating_tag = link_tag.select_one("span.rating")
                        episode_tag = link_tag.select_one("span.episode")
                        img_tag = link_tag.select_one("img")
                        
                        # Ekstrak anime_slug dari URL
                        rec_anime_slug = None
                        rec_url = link_tag.get('href', "N/A")
                        if rec_url != "N/A":
                            rec_anime_match = re.search(r'anime/([^/]+)', rec_url)
                            if rec_anime_match:
                                rec_anime_slug = rec_anime_match.group(1)
                        
                        recommendations_list.append({
                            "title": title_tag.text.strip() if title_tag else "N/A",
                            "url": rec_url,
                            "anime_slug": rec_anime_slug,
                            "cover_url": img_tag.get('src', "N/A") if img_tag else "N/A",
                            "rating": rating_tag.text.strip().replace("\n", " ") if rating_tag else "N/A",
                            "episode": episode_tag.text.strip() if episode_tag else "N/A"
                        })
            anime_details['recommendations'] = recommendations_list
            
            return anime_details
        
        except Exception as e:
            logger.error(f"Error getting anime details for {anime_slug}: {e}")
            return {}
    
    def get_episode_details(self, episode_url: str) -> Dict[str, Any]:
        """
        Get episode details from Samehadaku.
        """
        logger.info(f"Getting episode details from {episode_url}")
        
        try:
            soup = self.get_soup(episode_url)
            episode_data = {}
            
            # --- Informasi Episode ---
            title_tag = soup.select_one("h1.entry-title")
            episode_data['title'] = title_tag.text.strip() if title_tag else "N/A"
            
            # --- Informasi Rilis ---
            release_info_tag = soup.select_one(".sbdbti .time-post")
            episode_data['release_info'] = release_info_tag.text.strip() if release_info_tag else "N/A"
            
            # --- Navigasi Episode ---
            nav_container = soup.select_one('.naveps')
            next_episode_link = nav_container.select_one("a:has(i.fa-chevron-right)") if nav_container else None
            episode_data['navigation'] = {
                "previous_episode_url": nav_container.select_one("a:has(i.fa-chevron-left)")['href'] if nav_container and nav_container.select_one("a:has(i.fa-chevron-left)") else None,
                "all_episodes_url": nav_container.select_one(".nvsc a")['href'] if nav_container and nav_container.select_one(".nvsc a") else None,
                "next_episode_url": next_episode_link['href'] if next_episode_link and not next_episode_link.has_attr('class') else None
            }
            
            # --- Server Streaming ---
            streaming_servers = []
            server_options = soup.select("#server .east_player_option")
            post_id = server_options[0].get('data-post') if server_options else None
            
            if post_id:
                logger.info(f"Post ID found: {post_id}. Fetching stream links...")
                ajax_url = "https://v1.samehadaku.how/wp-admin/admin-ajax.php"
                ajax_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": episode_url
                }
                
                for option in server_options:
                    if nume := option.get('data-nume'):
                        server_name = option.find("span").get_text(strip=True) if option.find("span") else "Unknown Server"
                        
                        try:
                            payload = {'action': 'player_ajax', 'post': post_id, 'nume': nume, 'type': 'schtml'}
                            response = self.session.post(ajax_url, data=payload, headers=ajax_headers, timeout=10)
                            response.raise_for_status()
                            
                            embed_soup = BeautifulSoup(response.text, 'lxml')
                            iframe = embed_soup.find("iframe")
                            
                            if iframe and 'src' in iframe.attrs:
                                streaming_url = iframe['src']
                                logger.info(f"Link found for server: {server_name}")
                                
                                if "pixeldrain.com/u/" in streaming_url:
                                    file_id = streaming_url.split("pixeldrain.com/u/")[1]
                                    streaming_url = f"https://pixeldrain.com/api/file/{file_id}"
                                    logger.info(f"Converting Pixeldrain URL to: {streaming_url}")
                                
                                streaming_servers.append({
                                    "server_name": server_name,
                                    "streaming_url": streaming_url
                                })
                        except Exception as e:
                            logger.error(f"Failed to get link for server {server_name}: {e}")
            
            episode_data['streaming_servers'] = sorted(streaming_servers, key=lambda x: x['server_name'])
            
            # --- Link Download ---
            download_links = {}
            for container in soup.select(".download-eps"):
                if p_tag := container.find("p"):
                    format_type = p_tag.get_text(strip=True)
                    download_links[format_type] = {}
                    for item in container.select("li"):
                        if resolution_tag := item.find("strong"):
                            resolution = resolution_tag.get_text(strip=True)
                            providers = [{"provider": a.get_text(strip=True), "url": a.get('href')} for a in item.find_all("a")]
                            download_links[format_type][resolution] = providers
            
            episode_data['download_links'] = download_links
            
            # --- Anime Info Box (Synopsis, Thumbnail, etc.) ---
            anime_info_box = soup.select_one(".episodeinf .infoanime")
            if anime_info_box:
                episode_data['anime_info'] = {
                    "title": anime_info_box.select_one(".infox h2.entry-title").get_text(strip=True).replace("Sinopsis Anime", "").replace("Indo", "").strip() if anime_info_box.select_one(".infox h2.entry-title") else "N/A",
                    "thumbnail_url": anime_info_box.select_one(".thumb img").get("src") if anime_info_box.select_one(".thumb img") else "N/A",
                    "synopsis": anime_info_box.select_one(".desc .entry-content-single").get_text(strip=True) if anime_info_box.select_one(".desc .entry-content-single") else "N/A",
                    "genres": [tag.get_text(strip=True) for tag in anime_info_box.select(".genre-info a")]
                }
            else:
                episode_data['anime_info'] = {}
            
            # --- Other Episodes List ---
            other_episodes_list = []
            other_eps_container = soup.select_one(".episode-lainnya .lstepsiode ul")
            if other_eps_container:
                for item in other_eps_container.find_all("li"):
                    title_el = item.select_one(".lchx a")
                    other_episodes_list.append({
                        "title": title_el.get_text(strip=True) if title_el else "N/A",
                        "url": title_el.get("href") if title_el else "N/A",
                        "thumbnail_url": item.select_one(".epsright img").get("src") if item.select_one(".epsright img") else "N/A",
                        "release_date": item.select_one(".date").get_text(strip=True) if item.select_one(".date") else "N/A"
                    })
            episode_data['other_episodes'] = other_episodes_list
            
            return episode_data
        
        except Exception as e:
            logger.error(f"Error getting episode details for {episode_url}: {e}")
            return {}
    
    def get_anime_terbaru(self, page: int = 1) -> List[Dict[str, Any]]:
        """
        Get latest anime from Samehadaku.
        """
        url = f"{self.base_url}/anime-terbaru/page/{page}/" if page > 1 else f"{self.base_url}/anime-terbaru/"
        logger.info(f"Getting latest anime from {url}")
        
        try:
            soup = self.get_soup(url)
            anime_list = []
            
            # Cari semua artikel anime dengan selector yang benar
            articles = soup.select("div.post-show li")
            
            if not articles:
                logger.warning(f"No anime found on page {page}")
                return []
            
            for article in articles:
                title_tag = article.select_one("h2.entry-title a")
                cover_tag = article.select_one("img.npws")
                spans = article.select("div.dtla > span")
                
                if not title_tag:
                    continue
                
                title = title_tag.text.strip()
                anime_url = title_tag["href"] if title_tag else "N/A"
                cover_url = cover_tag["src"] if cover_tag and cover_tag.has_attr("src") else "N/A"
                
                episode_tag = spans[0].find("author") if len(spans) > 0 else None
                episode = episode_tag.text.strip() if episode_tag else "N/A"
                
                uploader_tag = spans[1].find("author") if len(spans) > 1 else None
                uploader = uploader_tag.text.strip() if uploader_tag else "N/A"
                
                release_tag = spans[2] if len(spans) > 2 else None
                release_time = release_tag.text.replace("Released on:", "").strip() if release_tag else "N/A"
                
                # Ekstrak anime_slug dari URL
                anime_slug = None
                if anime_url != "N/A":
                    anime_url_str = str(anime_url)
                    anime_match = re.search(r'anime/([^/]+)', anime_url_str)
                    if anime_match:
                        anime_slug = anime_match.group(1)
                    else:
                        episode_match = re.search(r'([^/]+)-episode-\d+', anime_url_str)
                        if episode_match:
                            anime_slug = episode_match.group(1)
                
                anime_list.append({
                    "judul": title,
                    "url": anime_url,
                    "anime_slug": anime_slug,
                    "episode": episode,
                    "uploader": uploader,
                    "rilis": release_time,
                    "cover": cover_url
                })
            
            return anime_list
        
        except Exception as e:
            logger.error(f"Error getting latest anime (page {page}): {e}")
            return []
    
    def get_movie_list(self, page: int = 1) -> List[Dict[str, Any]]:
        """
        Get movie list from Samehadaku.
        """
        url = f"{self.base_url}/anime-movie/page/{page}/" if page > 1 else f"{self.base_url}/anime-movie/"
        logger.info(f"Getting movie list from {url}")
        
        try:
            soup = self.get_soup(url)
            movie_list = []
            
            # Cari semua artikel movie dengan selector yang benar
            articles = soup.find_all("article", class_="animpost")
            
            if not articles:
                logger.warning(f"No movies found on page {page}")
                return []
            
            for article in articles:
                main_link_tag = article.find("a")
                url_movie = main_link_tag["href"] if main_link_tag else "N/A"
                title_tag = article.find("h2", class_="entry-title")
                title = title_tag.text.strip() if title_tag else "N/A"
                cover_tag = article.find("img")
                cover = cover_tag.get("src") if cover_tag else "N/A"
                status_tag = article.select_one("div.data .type")
                status = status_tag.text.strip() if status_tag else "N/A"
                score_tag = article.select_one("span.skor")
                score = score_tag.text.strip() if score_tag else "N/A"
                synopsis_tag = article.select_one("div.ttls")
                synopsis = synopsis_tag.text.strip() if synopsis_tag else "N/A"
                
                views = "N/A"
                metadata_spans = article.select("div.metadata span")
                for span in metadata_spans:
                    if "Views" in span.text:
                        views = span.text.strip()
                        break
                
                genre_tags = article.select("div.genres a")
                genres = [g.text.strip() for g in genre_tags] if genre_tags else []
                
                # Ekstrak anime_slug dari URL
                anime_slug = None
                if url_movie != "N/A":
                    anime_match = re.search(r'anime/([^/]+)', url_movie)
                    if anime_match:
                        anime_slug = anime_match.group(1)
                
                movie_list.append({
                    "judul": title,
                    "url": url_movie,
                    "anime_slug": anime_slug,
                    "status": status,
                    "skor": score,
                    "sinopsis": synopsis,
                    "views": views,
                    "cover": cover,
                    "genres": genres
                })
            
            return movie_list
        
        except Exception as e:
            logger.error(f"Error getting movie list (page {page}): {e}")
            return []
    
    def get_jadwal_rilis(self, day: Optional[str] = None) -> Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]:
        """
        Get release schedule from Samehadaku.
        """
        if day:
            # Jika hari tertentu diminta
            api_url = f"https://v1.samehadaku.how/wp-json/custom/v1/all-schedule?perpage=100&day={day.lower()}"
            logger.info(f"Getting release schedule for {day} from {api_url}")
            
            try:
                daily_schedule_raw = self.get_json(api_url)
                
                cleaned_schedule = []
                for item in daily_schedule_raw:
                    genres_raw = item.get("genre", "")
                    genres_list = []
                    if genres_raw and genres_raw != "N/A":
                        genres_list = [g.strip() for g in genres_raw.split(',')]
                    
                    # Ekstrak anime_slug dari URL
                    anime_slug = None
                    url = item.get("url", "N/A")
                    if url != "N/A":
                        anime_match = re.search(r'anime/([^/]+)', url)
                        if anime_match:
                            anime_slug = anime_match.group(1)
                    
                    cleaned_schedule.append({
                        "title": item.get("title", "N/A"),
                        "url": url,
                        "anime_slug": anime_slug,
                        "cover_url": item.get("featured_img_src", "N/A"),
                        "type": item.get("east_type", "N/A"),
                        "score": item.get("east_score", "N/A"),
                        "genres": genres_list,
                        "release_time": item.get("east_time", "N/A")
                    })
                
                return cleaned_schedule
            
            except Exception as e:
                logger.error(f"Error getting release schedule for {day}: {e}")
                return []
        
        else:
            # Jika semua hari diminta
            days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            full_schedule = {}
            
            logger.info("Getting release schedule for all days")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
                # Buat fungsi untuk mengambil jadwal untuk satu hari
                def fetch_schedule_for_day(day):
                    try:
                        schedule = self.get_jadwal_rilis(day)
                        return day.capitalize(), schedule
                    except Exception as e:
                        logger.error(f"Error getting schedule for {day}: {e}")
                        return day.capitalize(), []
                
                # Jalankan fungsi untuk semua hari secara paralel
                future_to_day = {executor.submit(fetch_schedule_for_day, day): day for day in days_of_week}
                
                # Kumpulkan hasil
                for future in concurrent.futures.as_completed(future_to_day):
                    day, schedule = future.result()
                    full_schedule[day] = schedule
            
            # Urutkan hasil
            sorted_schedule = {day.capitalize(): full_schedule[day.capitalize()] for day in days_of_week}
            return sorted_schedule
    
    def get_home_data(self) -> Dict[str, Any]:
        """
        Get home page data from Samehadaku.
        """
        logger.info(f"Getting home page data from {self.base_url}")
        
        try:
            # Ambil HTML dari URL hanya sekali
            soup = self.get_soup(self.base_url)
            
            # Log HTML untuk debugging
            html_content = soup.prettify()
            logger.info(f"HTML structure length: {len(html_content)}")
            logger.info(f"HTML structure (first 1000 chars): {html_content[:1000]}...")
            
            # Log semua div classes untuk debugging
            div_classes = set()
            for div in soup.find_all('div', class_=True):
                div_classes.update(div['class'])
            logger.info(f"All div classes found: {sorted(list(div_classes))}")
            
            # Log semua article classes untuk debugging
            article_classes = set()
            for article in soup.find_all('article', class_=True):
                article_classes.update(article['class'])
            logger.info(f"All article classes found: {sorted(list(article_classes))}")
            
            # Jalankan semua fungsi scraping secara paralel
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Buat fungsi untuk mengambil data anime terbaru dari soup
                def get_anime_terbaru_from_soup(soup):
                    try:
                        anime_list = []
                        # Log selectors untuk debugging
                        logger.info("Mencari anime terbaru dengan selector: .post-show > ul > li")
                        items = soup.select(".post-show > ul > li")
                        logger.info(f"Jumlah item anime terbaru yang ditemukan: {len(items)}")
                        
                        for li in items:
                            title_el = li.select_one("h2.entry-title a")
                            if not title_el:
                                continue
                            
                            # Mengambil episode dengan selector yang lebih stabil
                            episode_el = li.select_one(".dtla span:nth-of-type(1)")
                            episode = episode_el.get_text(strip=True).replace("Episode", "").strip() if episode_el else "-"
                            
                            # Mengambil tanggal rilis
                            released_on_el = li.select_one(".dtla span:nth-of-type(3)")
                            rilis = released_on_el.get_text(strip=True).replace("Released on:", "").strip() if released_on_el else "-"
                            
                            url = title_el["href"]
                            cover = li.select_one("img")["src"] if li.select_one("img") else "-"
                            
                            # Ekstrak anime_slug dari URL
                            anime_slug = None
                            if url != "N/A" and url != "-":
                                anime_match = re.search(r'anime/([^/]+)', url)
                                if anime_match:
                                    anime_slug = anime_match.group(1)
                            
                            anime_list.append({
                                "judul": title_el.text.strip(),
                                "url": url,
                                "anime_slug": anime_slug,
                                "episode": episode,
                                "rilis": rilis,
                                "cover": cover
                            })
                        
                        return anime_list
                    except Exception as e:
                        logger.error(f"Error getting anime terbaru from soup: {e}")
                        return []
                
                # Buat fungsi untuk mengambil data movie dari soup
                def get_movie_from_soup(soup):
                    try:
                        movie_list = []
                        # Log selectors untuk debugging
                        logger.info("Mencari movie dengan selector: aside#sidebar .widgetseries ul li")
                        movie_items = soup.select("aside#sidebar .widgetseries ul li")
                        logger.info(f"Jumlah item movie yang ditemukan: {len(movie_items)}")
                        
                        for item in movie_items:
                            title_el = item.select_one("h2 a.series")
                            if not title_el:
                                continue
                            
                            # Mengambil genre
                            genre_elements = item.select(".lftinfo span a")
                            genres = [genre.text.strip() for genre in genre_elements]
                            
                            # Mengambil tanggal rilis
                            release_date_el = item.select_one(".lftinfo span:last-of-type")
                            release_date = release_date_el.text.strip() if release_date_el and not release_date_el.find('a') else "-"
                            
                            url = title_el.get("href")
                            cover = item.select_one("img").get("src") if item.select_one("img") else "-"
                            
                            # Ekstrak anime_slug dari URL
                            anime_slug = None
                            if url != "N/A" and url != "-":
                                anime_match = re.search(r'anime/([^/]+)', url)
                                if anime_match:
                                    anime_slug = anime_match.group(1)
                            
                            movie_list.append({
                                "judul": title_el.text.strip(),
                                "url": url,
                                "anime_slug": anime_slug,
                                "tanggal": release_date,
                                "cover": cover,
                                "genres": genres
                            })
                        
                        return movie_list
                    except Exception as e:
                        logger.error(f"Error getting movie from soup: {e}")
                        return []
                
                # Buat fungsi untuk mengambil data anime mingguan dari soup
                def get_anime_mingguan_from_soup(soup):
                    try:
                        anime_list = []
                        # Log selectors untuk debugging
                        logger.info("Mencari anime mingguan dengan selector: div.topten-animesu li")
                        items = soup.select("div.topten-animesu li")
                        if not items:
                            # Coba selector alternatif jika tidak ada hasil
                            logger.info("Mencoba selector alternatif untuk anime mingguan: div.topten-animesu-left li, div.topten-animesu-right li")
                            items = soup.select("div.topten-animesu-left li, div.topten-animesu-right li")
                        logger.info(f"Jumlah item anime mingguan yang ditemukan: {len(items)}")
                        
                        for item in items:
                            title_el = item.select_one("h2 a")
                            if not title_el:
                                # Coba selector alternatif untuk judul
                                title_el = item.select_one("a.series")
                                if not title_el:
                                    continue
                            
                            # Mengambil rating
                            rating_el = item.select_one(".rating")
                            rating = rating_el.text.strip() if rating_el else "-"
                            
                            # Mengambil genre
                            genre_elements = item.select(".lftinfo span a")
                            genres = [genre.text.strip() for genre in genre_elements]
                            
                            url = title_el.get("href")
                            cover = item.select_one("img").get("src") if item.select_one("img") else "-"
                            
                            # Ekstrak anime_slug dari URL
                            anime_slug = None
                            if url and url != "N/A" and url != "-":
                                anime_match = re.search(r'anime/([^/]+)', url)
                                if anime_match:
                                    anime_slug = anime_match.group(1)
                            
                            # Debug log untuk membantu troubleshooting
                            full_title = title_el.text.strip() if hasattr(title_el, 'text') else 'Unknown'
                            logger.info(f"Extracted top10 item: {full_title}")
                            
                            # Ekstrak hanya nama anime dari judul
                            # Format judul biasanya: "8.73\n\nTOP1\nOne Piece"
                            anime_name = full_title
                            if "\n" in full_title:
                                # Ambil baris terakhir yang berisi nama anime
                                anime_name = full_title.split("\n")[-1].strip()
                            
                            anime_list.append({
                                "judul": anime_name,
                                "url": url if url else "-",
                                "anime_slug": anime_slug,
                                "rating": rating,
                                "cover": cover,
                                "genres": genres
                            })
                        
                        return anime_list
                    except Exception as e:
                        logger.error(f"Error getting anime mingguan from soup: {e}")
                        return []
                
                # Jalankan semua fungsi secara paralel
                future_anime_terbaru = executor.submit(get_anime_terbaru_from_soup, soup)
                future_movie = executor.submit(get_movie_from_soup, soup)
                future_anime_mingguan = executor.submit(get_anime_mingguan_from_soup, soup)
                
                # Ambil jadwal rilis secara terpisah karena menggunakan API
                future_jadwal_rilis = executor.submit(self.get_jadwal_rilis)
                
                # Kumpulkan hasil
                anime_terbaru_home = future_anime_terbaru.result()
                movie_home = future_movie.result()
                anime_mingguan = future_anime_mingguan.result()
                jadwal_rilis_home = future_jadwal_rilis.result()
            
            # Buat hasil akhir
            return {
                "top10": anime_mingguan,
                "new_eps": anime_terbaru_home,
                "movies": movie_home,
                "jadwal_rilis": jadwal_rilis_home
            }
        
        except Exception as e:
            logger.error(f"Error getting home page data: {e}")
            return {
                "top10": [],
                "new_eps": [],
                "movies": [],
                "jadwal_rilis": {}
            }