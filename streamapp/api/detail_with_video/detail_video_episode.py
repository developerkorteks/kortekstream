import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging

# Konfigurasi logging untuk output yang lebih informatif
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_stream_url(session, ajax_url, payload, headers, server_name):
    """Fungsi untuk mengambil satu URL streaming dari server."""
    try:
        response = session.post(ajax_url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        embed_soup = BeautifulSoup(response.text, 'lxml')
        iframe = embed_soup.find("iframe")
        
        if iframe and 'src' in iframe.attrs:
            streaming_url = iframe['src']
            logging.info(f"✅ Link ditemukan untuk server: {server_name}")
            
            # Tambahan: Konversi URL Pixeldrain jika perlu
            if "pixeldrain.com/u/" in streaming_url:
                file_id = streaming_url.split("pixeldrain.com/u/")[1]
                streaming_url = f"https://pixeldrain.com/api/file/{file_id}"
                logging.info(f"      Mengubah URL Pixeldrain ke: {streaming_url}")

            return {"server_name": server_name, "streaming_url": streaming_url}
        else:
            logging.warning(f"⚠️ Respon diterima dari {server_name}, tapi tidak ada iframe ditemukan.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Gagal mengambil link untuk server {server_name}: {e}")
        return None

def scrape_episode_details(url):
    """
    Scrape semua detail episode dari URL yang diberikan secara efisien.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Referer": "https://v1.samehadaku.how/"
    }
    
    session = requests.Session()
    
    try:
        logging.info(f"⚙️ Mengambil data awal dari: {url}")
        initial_res = session.get(url, headers=headers, timeout=15)
        initial_res.raise_for_status()
        soup = BeautifulSoup(initial_res.text, "lxml")
    except requests.exceptions.RequestException as e:
        logging.critical(f"❌ Gagal memuat halaman utama: {e}")
        return None

    episode_details = {}

    # Ekstraksi Informasi Dasar
    episode_details['title'] = soup.select_one("h1.entry-title").get_text(strip=True) if soup.select_one("h1.entry-title") else "Judul Tidak Ditemukan"
    episode_details['release_info'] = soup.select_one(".sbdbti .time-post").get_text(strip=True) if soup.select_one(".sbdbti .time-post") else "N/A"
    
    # Ekstraksi Navigasi
    nav_container = soup.select_one('.naveps')
    episode_details['navigation'] = {
        "previous_episode_url": nav_container.select_one("a:has(i.fa-chevron-left)")['href'] if nav_container and nav_container.select_one("a:has(i.fa-chevron-left)") else None,
        "all_episodes_url": nav_container.select_one(".nvsc a")['href'] if nav_container and nav_container.select_one(".nvsc a") else None,
        "next_episode_url": nav_container.select_one("a:has(i.fa-chevron-right)")['href'] if nav_container and nav_container.select_one("a:has(i.fa-chevron-right)") else None
    }

    # Pengambilan Link Streaming
    streaming_servers = []
    server_options = soup.select("#server .east_player_option")
    post_id = server_options[0].get('data-post') if server_options else None
    
    if post_id:
        logging.info(f"✅ Post ID ditemukan: {post_id}. Memulai pengambilan link streaming...")
        ajax_url = "https://v1.samehadaku.how/wp-admin/admin-ajax.php"
        ajax_headers = {**headers, "X-Requested-With": "XMLHttpRequest", "Referer": url}

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for option in server_options:
                # --- INI BAGIAN YANG DIPERBAIKI ---
                # Hanya ambil teks dari dalam tag <span>
                server_name_tag = option.find("span")
                server_name = server_name_tag.get_text(strip=True) if server_name_tag else "Server Tidak Diketahui"
                # ------------------------------------
                
                server_nume = option.get('data-nume')
                if not server_nume: continue
                
                payload = {'action': 'player_ajax', 'post': post_id, 'nume': server_nume, 'type': 'schtml'}
                futures.append(executor.submit(fetch_stream_url, session, ajax_url, payload, ajax_headers, server_name))
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    streaming_servers.append(result)
    else:
        logging.warning("⚠️ Post ID tidak ditemukan. Tidak dapat mengambil link streaming.")

    episode_details['streaming_servers'] = sorted(streaming_servers, key=lambda x: x['server_name'])

    # Ekstraksi Link Download
    download_links = {}
    for container in soup.select(".download-eps"):
        format_type = container.find("p").get_text(strip=True)
        download_links[format_type] = {}
        for item in container.select("li"):
            resolution = item.find("strong").get_text(strip=True)
            providers = [{"provider": a.get_text(strip=True), "url": a.get('href')} for a in item.find_all("a")]
            download_links[format_type][resolution] = providers
            
    episode_details['download_links'] = download_links
    
    return episode_details

# --- CONTOH PENGGUNAAN ---
if __name__ == "__main__":
    target_url = "https://v1.samehadaku.how/one-piece-episode-1136/"
    
    start_time = time.time()
    scraped_data = scrape_episode_details(target_url)
    end_time = time.time()

    if scraped_data:
        print("\n" + "="*50)
        print("✅ Data episode berhasil di-scrape!")
        print("="*50)
        print(json.dumps(scraped_data, indent=4, ensure_ascii=False))
        
        if not scraped_data.get('streaming_servers'):
            print("\n⚠️ PERHATIAN: Tidak ada link streaming yang berhasil diambil.")
            
    else:
        print("\n❌ Gagal men-scrape data dari URL yang diberikan.")

    print(f"\n🚀 Selesai dalam {end_time - start_time:.2f} detik")