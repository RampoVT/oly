import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

SOURCE_URL = "https://raw.githubusercontent.com/fleung49/star/refs/heads/main/OLY"
M3U_FILE = "playlist.m3u"
MD_FILE = "README.md"
MAX_WORKERS = 20  # Number of simultaneous checks

def check_link(url):
    """Checks link status; returns True if active."""
    try:
        # Using a 5-second timeout for each individual check
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def process_channel(name, url, genre):
    """Logic to determine group and status for a single channel."""
    is_active = check_link(url)
    
    # Priority Grouping: 
    # 1. Rocket group for specific domain
    # 2. Offline group if link is dead
    # 3. Original genre for active non-rocket links
    if "s.rocketdns.info:8080" in url:
        group = "Rocket"
    elif not is_active:
        group = "Offline"
    else:
        group = genre
        
    return {
        "name": name,
        "url": url,
        "group": group,
        "active": is_active,
        "original_genre": genre
    }

def main():
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
                name, url = line.split(",", 1)
                channels_to_check.append((name.strip(), url.strip(), current_genre))

        # Speed up: Check channels in parallel
        print(f"Checking {len(channels_to_check)} channels using {MAX_WORKERS} threads...")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(lambda p: process_channel(*p), channels_to_check))

        # Build M3U and Markdown content
        m3u_lines = ["#EXTM3U"]
        md_lines = [
            "# 📺 Channel Status Dashboard",
            f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n",
            "| Status | Channel Name | Current Group | Original Category |",
            "| :---: | :--- | :--- | :--- |"
        ]

        for res in results:
            # Add to M3U
            m3u_lines.append(f'#EXTINF:-1 group-title="{res["group"]}",{res["name"]}')
            m3u_lines.append(res["url"])
            
            # Add to Markdown
            icon = "✅" if res["active"] else "❌"
            md_lines.append(f"| {icon} | {res['name']} | **{res['group']}** | {res['original_genre']} |")

        # Save files
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        with open(MD_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
            
        print("Update complete.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
