import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from thefuzz import process as fuzzy_process

# File paths and URLs
SOURCE_URL = "https://raw.githubusercontent.com/fleung49/star/refs/heads/main/OLY"
EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz"
EPG_DATA_FILE = "epg_ripper_ALL_SOURCES1.txt"
M3U_FILE = "playlist.m3u"
MD_FILE = "README.md"

MAX_WORKERS = 25 

def load_epg_ids():
    """Reads the EPG text file and returns a list of available IDs."""
    try:
        with open(EPG_DATA_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("--")]
    except FileNotFoundError:
        print("EPG text file not found. Skipping EPG mapping.")
        return []

def check_link(url):
    """Checks link status using a player-like User-Agent and GET request."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (VLC; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        # Using stream=True with a GET request for better reliability on IPTV panels
        response = requests.get(url, headers=headers, timeout=7, stream=True, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def process_channel(name, url, genre, epg_list):
    """Determines status, group, and best EPG match."""
    is_active = check_link(url)
    
    # Priority Grouping Logic
    if "s.rocketdns.info:8080" in url:
        group = "Rocket"
    elif not is_active:
        group = "Offline"
    else:
        group = genre

    # Auto-EPG Fuzzy Matching
    best_match = ""
    if epg_list:
        match, score = fuzzy_process.extractOne(name, epg_list)
        if score > 75: # Matching threshold
            best_match = match
        
    return {
        "name": name, "url": url, "group": group, 
        "active": is_active, "genre": genre, "tvg_id": best_match
    }

def main():
    epg_ids = load_epg_ids()
    
    try:
        response = requests.get(SOURCE_URL)
        response.raise_for_status()
        lines = response.text.splitlines()

        channels_to_check = []
        current_genre = "General"

        for line in lines:
            line = line.strip()
            if not line: continue
            if ",#genre#" in line:
                current_genre = line.split(",#genre#")[0].strip()
                continue
            if "," in line:
                parts = line.split(",", 1)
                name = parts[0].strip()
                url = parts[1].strip()
                channels_to_check.append((name, url, current_genre))

        print(f"Syncing {len(channels_to_check)} channels and checking status...")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(lambda p: process_channel(*p, epg_ids), channels_to_check))

        # 1. Generate M3U with EPG Link in Header
        m3u_lines = [f'#EXTM3U x-tvg-url="{EPG_URL}"']
        for res in results:
            m3u_lines.append(f'#EXTINF:-1 tvg-id="{res["tvg_id"]}" group-title="{res["group"]}",{res["name"]}')
            m3u_lines.append(res["url"])
            
        # 2. Generate Markdown Dashboard
        md_lines = [
            "# 📺 Channel Status Dashboard",
            f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n",
            "| Status | Channel | Final Group | EPG ID |",
            "| :---: | :--- | :--- | :--- |"
        ]
        for res in results:
            icon = "✅" if res["active"] else "❌"
            md_lines.append(f"| {icon} | {res['name']} | **{res['group']}** | `{res['tvg_id']}` |")

        # Save files
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        with open(MD_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
            
        print(f"Successfully updated {M3U_FILE} and {MD_FILE}.")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()
