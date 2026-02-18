import requests
from datetime import datetime

# Source URL for the OLY file
SOURCE_URL = "https://raw.githubusercontent.com/fleung49/star/refs/heads/main/OLY"
M3U_FILE = "playlist.m3u"
MD_FILE = "README.md"

def check_link(url):
    """Checks if a URL is active with a 5-second timeout."""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def main():
    try:
        response = requests.get(SOURCE_URL)
        response.raise_for_status()
        lines = response.text.splitlines()

        m3u_lines = ["#EXTM3U"]
        md_lines = [
            "# 📺 Channel Status Dashboard",
            f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n",
            "| Status | Channel Name | Final Group | Original Category |",
            "| :---: | :--- | :--- | :--- |"
        ]

        current_genre = "General"

        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Identify Genre headers from the OLY format
            if ",#genre#" in line:
                current_genre = line.split(",#genre#")[0].strip()
                continue
            
            # Parse Channel Name and URL
            if "," in line:
                name, url = line.split(",", 1)
                name = name.strip()
                url = url.strip()
                
                is_active = check_link(url)
                
                # Grouping Logic:
                # 1. Rocket group for specific domain
                # 2. Offline group if link is dead
                # 3. Original genre for active non-rocket links
                if "s.rocketdns.info:8080" in url:
                    status_group = "Rocket"
                elif not is_active:
                    status_group = "Offline"
                else:
                    status_group = current_genre
                
                # Add to M3U Playlist
                m3u_lines.append(f'#EXTINF:-1 group-title="{status_group}",{name}')
                m3u_lines.append(url)
                
                # Add to Markdown Dashboard
                status_icon = "✅" if is_active else "❌"
                md_lines.append(f"| {status_icon} | {name} | **{status_group}** | {current_genre} |")

        # Save files
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
            
        with open(MD_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
            
        print("Updated playlist and status dashboard with Rocket grouping.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
