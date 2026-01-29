import os
import datetime
import json
import re
from xml.etree import ElementTree as ET
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ========= CONFIG =========
RSS_FILE = "index.xml"   # Path to your RSS feed file
MODEL = "gpt-4o-mini"    # Use GPT-4o-mini (or gpt-4o, gpt-5 if available)

# Validate API key exists
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError(
        "OPENAI_API_KEY environment variable is not set.\n"
        "Please set it in your environment or .env file."
    )

# SSL verification - set to False if behind corporate proxy
# Add VERIFY_SSL=false to your .env file if you get SSL certificate errors
verify_ssl = os.getenv("VERIFY_SSL", "true").lower() != "false"

import httpx
client = OpenAI(
    api_key=api_key,
    http_client=httpx.Client(verify=verify_ssl) if not verify_ssl else None
)
# ==========================

MAX_TOKENS = 400
TEMPERATURE = 1.2  # Higher temperature for more variability (default: 1.0)
TOP_P = 0.95       # Nucleus sampling for diverse outputs

BASE_PROMPT = """
You are a music expert. Provide ONE daily Apple Music album recommendation in this strict JSON format:

Rules:
- Do NOT repeat any artist or album from the list provided. 
- Prioritize rock and pop genres and favor diversity in sub-genres of that.
- Favor diversity in decade and geography.
- Highlight something exceptional or legendary.
- Consider deep cuts, cult classics, and underrated gems from different eras.
- Be creative and think outside the box.

{
  "artist": "Artist Name",
  "album": "Album Title",
  "release_date": "Month DD, YYYY",
  "link": "https://music.apple.com/",
  "description": "A short paragraph explaining why this album is exceptional."
}

Note: Use the generic Apple Music homepage URL for the link field.
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
    """Fetch a fresh album recommendation, avoiding duplicates and handling malformed JSON."""
    recent_albums = get_recent_albums(30)
    history_context = "Albums already recommended: " + ", ".join(recent_albums)

    for attempt in range(3):  # up to 3 tries if bad JSON or duplicates
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": f"{BASE_PROMPT}\n\n{history_context}"
                    },
                    {
                        "role": "user", 
                        "content": "Please recommend one album following the rules above."
                    }
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P
            )
            content = response.choices[0].message.content.strip()
            if not content:
                print("⚠️ Empty response from API, retrying...")
                continue

            # Remove Markdown fences if present
            content = re.sub(r"^```(json)?|```$", "", content).strip()

            # Try parsing JSON
            album = json.loads(content)

            full_title = f"{album['artist']} - {album['album']}"
            if full_title not in recent_albums:
                return album
            else:
                print(f"⚠️ Duplicate detected ({full_title}), retrying...")

        except json.JSONDecodeError:
            print(f"⚠️ JSON parse error on attempt {attempt+1}. Raw content:\n{content}\nRetrying...")
            continue
        except ConnectionError as e:
            print(f"❌ Network connection error on attempt {attempt+1}: {e}")
            print("   Check your internet connection and try again.")
            if attempt == 2:  # Last attempt
                raise
            continue
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"⚠️ {error_type} on attempt {attempt+1}: {error_msg}")
            
            # Provide specific guidance for common errors
            if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                print("   → Check that your OPENAI_API_KEY is valid and active.")
            elif "rate limit" in error_msg.lower():
                print("   → You've hit the API rate limit. Wait a moment before retrying.")
            elif "timeout" in error_msg.lower():
                print("   → Request timed out. Check your internet connection.")
            
            if attempt == 2:  # Last attempt
                raise
            continue

    raise RuntimeError("Could not generate valid album JSON after 3 attempts.")

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
