import os
import datetime
import json
from xml.etree import ElementTree as ET
from openai import OpenAI

# ========= CONFIG =========
RSS_FILE = "index.xml"   # Path to your RSS feed file
MODEL = "gpt-4o-mini"    # Use GPT-4o-mini (or gpt-4o, gpt-5 if available)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# ==========================

PROMPT = """
You are a music expert. Provide ONE daily Apple Music album recommendation in this strict JSON format:

Rules:
- Do NOT repeat any artist or album from the list provided.
- Favor diversity in genre, decade, and geography.
- Highlight something exceptional, overlooked, or legendary.

{
  "artist": "Artist Name",
  "album": "Album Title",
  "release_date": "Month DD, YYYY",
  "link": "https://music.apple.com/...",
  "description": "A short paragraph explaining why this album is exceptional."
}
"""

def get_recent_albums(days=30):
    """Extract recently recommended albums from RSS feed (by title)."""
    if not os.path.exists(RSS_FILE):
        return []
    
    tree = ET.parse(RSS_FILE)
    root = tree.getroot()
    channel = root.find("channel")
    items = channel.findall("item")

    recent_titles = []
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)

    for item in items:
        title = item.find("title").text if item.find("title") is not None else None
        pubdate = item.find("pubDate").text if item.find("pubDate") is not None else None

        if title and pubdate:
            try:
                parsed_date = datetime.datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S EST")
            except ValueError:
                parsed_date = None

            if not parsed_date or parsed_date >= cutoff_date:
                recent_titles.append(title)

    return recent_titles

def get_daily_album():
    """Fetch a fresh album recommendation, avoiding duplicates."""
    recent_albums = get_recent_albums(30)
    history_context = "Albums already recommended: " + ", ".join(recent_albums)

    for attempt in range(3):  # up to 3 tries if duplicates slip through
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": BASE_PROMPT},
                {"role": "user", "content": history_context}
            ],
            max_tokens=400
        )
        content = response.choices[0].message.content
        album = json.loads(content)

        full_title = f"{album['artist']} - {album['album']}"
        if full_title not in recent_albums:
            return album
        else:
            print(f"⚠️ Duplicate detected ({full_title}), retrying...")

    raise RuntimeError("Could not generate a unique album after 3 attempts")

def add_item_to_rss(album):
    """Insert a new <item> into the RSS feed."""
    if not os.path.exists(RSS_FILE):
        rss_template = """<?xml version="1.0" encoding="UTF-8"?>
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

    item = ET.Element("item")
    ET.SubElement(item, "title").text = f"{album['artist']} - {album['album']}"
    ET.SubElement(item, "link").text = album["link"]
    ET.SubElement(item, "guid").text = album["link"]
    ET.SubElement(item, "description").text = (
        f"Release Date: {album['release_date']}\nWhy it’s exceptional: {album['description']}"
    )
    ET.SubElement(item, "pubDate").text = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S EST")

    channel.insert(0, item)
    tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    album = get_daily_album()
    add_item_to_rss(album)
    print(f"✅ Added: {album['artist']} - {album['album']}")
