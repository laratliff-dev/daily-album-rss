import os
import datetime
import openai
from xml.etree import ElementTree as ET

# ========= CONFIG =========
RSS_FILE = "index.xml"   # Path to your RSS feed file
MODEL = "gpt-5"          # Use GPT-5 for recommendations
openai.api_key = os.getenv("OPENAI_API_KEY")
# ==========================

PROMPT = """
You are a music expert. Provide ONE daily Apple Music album recommendation in this strict JSON format:

{
  "artist": "Artist Name",
  "album": "Album Title",
  "release_date": "Month DD, YYYY",
  "link": "https://music.apple.com/...",
  "description": "A short paragraph explaining why this album is exceptional."
}
"""

def get_daily_album():
    """Fetch a fresh album recommendation from OpenAI."""
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "system", "content": PROMPT}],
        max_tokens=400
    )

    content = response["choices"][0]["message"]["content"]

    # Parse JSON safely
    import json
    album = json.loads(content)
    return album

def add_item_to_rss(album):
    """Insert a new <item> into the RSS feed."""
    if not os.path.exists(RSS_FILE):
        # Create a basic RSS skeleton if file doesn't exist
        rss_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Daily Album Picks</title>
    <link>https://music.apple.com/</link>
    <description>Curated daily Apple Music album highlights.</description>
  </channel>
</rss>
"""
        with open(RSS_FILE, "w", encoding="utf-8") as f:
            f.write(rss_template)

    tree = ET.parse(RSS_FILE)
    root = tree.getroot()
    channel = root.find("channel")

    # Create item
    item = ET.Element("item")
    ET.SubElement(item, "title").text = f"{album['artist']} - {album['album']}"
    ET.SubElement(item, "link").text = album["link"]
    ET.SubElement(item, "guid").text = album["link"]
    ET.SubElement(item, "description").text = (
        f"Release Date: {album['release_date']}\nWhy it’s exceptional: {album['description']}"
    )
    ET.SubElement(item, "pubDate").text = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S EST")

    # Insert new item at top
    channel.insert(0, item)

    # Save file
    tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    album = get_daily_album()
    add_item_to_rss(album)
    print(f"✅ Added: {album['artist']} - {album['album']}")
