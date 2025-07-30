import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging

# Set up informative logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_stream_url(session, ajax_url, payload, headers, server_name):
    """Fetches a single streaming URL from the server."""
    try:
        response = session.post(ajax_url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        embed_soup = BeautifulSoup(response.text, 'lxml')
        iframe = embed_soup.find("iframe")
        
        if iframe and 'src' in iframe.attrs:
            streaming_url = iframe['src']
            logging.info(f"✅ Link found for server: {server_name}")
            
            if "pixeldrain.com/u/" in streaming_url:
                file_id = streaming_url.split("pixeldrain.com/u/")[1]
                streaming_url = f"https://pixeldrain.com/api/file/{file_id}"
                logging.info(f"      Converting Pixeldrain URL to: {streaming_url}")

            return {"server_name": server_name, "streaming_url": streaming_url}
        else:
            logging.warning(f"⚠️ Response received from {server_name}, but no iframe was found.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Failed to get link for server {server_name}: {e}")
        return None

def scrape_episode_details(url):
    """
    Efficiently scrapes all details from a given episode URL,
    including synopsis, thumbnails, and other related episodes.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Referer": "https://v1.samehadaku.how/"
    }
    
    session = requests.Session()
    
    try:
        logging.info(f"⚙️ Fetching initial data from: {url}")
        initial_res = session.get(url, headers=headers, timeout=15)
        initial_res.raise_for_status()
        soup = BeautifulSoup(initial_res.text, "lxml")
    except requests.exceptions.RequestException as e:
        logging.critical(f"❌ Failed to load the main page: {e}")
        return None

    episode_details = {}

    # --- Basic Info Extraction ---
    episode_details['title'] = soup.select_one("h1.entry-title").get_text(strip=True) if soup.select_one("h1.entry-title") else "Title Not Found"
    episode_details['release_info'] = soup.select_one(".sbdbti .time-post").get_text(strip=True) if soup.select_one(".sbdbti .time-post") else "N/A"
    
    # --- Navigation Extraction ---
    nav_container = soup.select_one('.naveps')
    next_episode_link = nav_container.select_one("a:has(i.fa-chevron-right)") if nav_container else None
    episode_details['navigation'] = {
        "previous_episode_url": nav_container.select_one("a:has(i.fa-chevron-left)")['href'] if nav_container and nav_container.select_one("a:has(i.fa-chevron-left)") else None,
        "all_episodes_url": nav_container.select_one(".nvsc a")['href'] if nav_container and nav_container.select_one(".nvsc a") else None,
        "next_episode_url": next_episode_link['href'] if next_episode_link and not next_episode_link.has_attr('class') else None
    }

    # --- Streaming Link Extraction ---
    streaming_servers = []
    server_options = soup.select("#server .east_player_option")
    post_id = server_options[0].get('data-post') if server_options else None
    
    if post_id:
        logging.info(f"✅ Post ID found: {post_id}. Starting parallel stream link fetching...")
        ajax_url = "https://v1.samehadaku.how/wp-admin/admin-ajax.php"
        ajax_headers = {**headers, "X-Requested-With": "XMLHttpRequest", "Referer": url}

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    fetch_stream_url, 
                    session, 
                    ajax_url, 
                    {'action': 'player_ajax', 'post': post_id, 'nume': option.get('data-nume'), 'type': 'schtml'}, 
                    ajax_headers, 
                    option.find("span").get_text(strip=True) if option.find("span") else "Unknown Server"
                )
                for option in server_options if option.get('data-nume')
            ]
            
            for future in as_completed(futures):
                if result := future.result():
                    streaming_servers.append(result)
    else:
        logging.warning("⚠️ Post ID not found. Cannot fetch streaming links.")

    episode_details['streaming_servers'] = sorted(streaming_servers, key=lambda x: x['server_name'])

    # --- Download Link Extraction ---
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
            
    episode_details['download_links'] = download_links

    # --- Anime Info Box (Synopsis, Thumbnail, etc.) Extraction ---
    anime_info_box = soup.select_one(".episodeinf .infoanime")
    if anime_info_box:
        episode_details['anime_info'] = {
            "title": anime_info_box.select_one(".infox h2.entry-title").get_text(strip=True).replace("Sinopsis Anime", "").replace("Indo", "").strip() if anime_info_box.select_one(".infox h2.entry-title") else "N/A",
            "thumbnail_url": anime_info_box.select_one(".thumb img").get("src") if anime_info_box.select_one(".thumb img") else "N/A",
            "synopsis": anime_info_box.select_one(".desc .entry-content-single").get_text(strip=True) if anime_info_box.select_one(".desc .entry-content-single") else "N/A",
            "genres": [tag.get_text(strip=True) for tag in anime_info_box.select(".genre-info a")]
        }
    else:
        episode_details['anime_info'] = {}

    # --- Other Episodes List Extraction ---
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
    episode_details['other_episodes'] = other_episodes_list
    
    return episode_details

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    target_url = "https://v1.samehadaku.how/jidou-hanbaiki-ni-umarekawatta-season-2-episode-5/"
    
    start_time = time.time()
    scraped_data = scrape_episode_details(target_url)
    end_time = time.time()

    if scraped_data:
        print("\n" + "="*50)
        print("✅ Episode data scraped successfully!")
        print("="*50)
        print(json.dumps(scraped_data, indent=4, ensure_ascii=False))
        
        if not scraped_data.get('streaming_servers'):
            print("\n⚠️ ATTENTION: No streaming links were successfully retrieved.")
            
    else:
        print("\n❌ Failed to scrape data from the provided URL.")

    print(f"\n🚀 Completed in {end_time - start_time:.2f} seconds")