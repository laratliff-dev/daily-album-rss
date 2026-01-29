# Daily Album RSS

An automated daily album recommendation system that uses OpenAI's GPT models to generate curated music album suggestions and publishes them as an RSS feed.

## Overview

This application leverages AI to discover and recommend exceptional music albums with a focus on rock music and diversity across sub-genres, decades, and geography. Each day, it generates a new album recommendation with context about why it's worth listening to, ensuring no duplicates appear in the recent history.

## Features

- **AI-Powered Recommendations**: Uses OpenAI's GPT-4o-mini to generate thoughtful album suggestions
- **Duplicate Prevention**: Tracks the last 30 days of recommendations to ensure variety
- **RSS Feed Generation**: Automatically updates an RSS feed (index.xml) with new recommendations
- **Apple Music Integration**: Each recommendation includes an Apple Music link
- **Robust Error Handling**: Retries on JSON parsing errors or duplicate detections

## How It Works

1. Reads the existing RSS feed to extract recently recommended albums
2. Queries OpenAI's API with a custom prompt emphasizing rock music diversity and exceptional albums
3. Validates the response and checks for duplicates
4. Adds the new recommendation to the RSS feed with publication date and description

## Setup

### Prerequisites

- Python 3.x
- An OpenAI API key

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/laratliff-dev/daily-album-rss.git
   cd daily-album-rss
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key as an environment variable:
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="your-api-key-here"
   
   # Linux/Mac
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Usage

Run the script to generate a new daily album recommendation:

```bash
python album_feed.py
```

The script will:
- Generate a new album recommendation
- Add it to `index.xml` (creates the file if it doesn't exist)
- Display a confirmation message

## RSS Feed Structure

Each RSS item includes:
- **Title**: Artist - Album
- **Link**: Direct link to the album on Apple Music
- **Description**: Release date and explanation of why the album is exceptional
- **Publication Date**: When the recommendation was added

## Configuration

You can modify the behavior in `album_feed.py`:
- `MODEL`: Change the OpenAI model (default: `gpt-4o-mini`)
- `RSS_FILE`: Change the RSS feed filename (default: `index.xml`)
- `BASE_PROMPT`: Customize the recommendation criteria
- `days` parameter in `get_recent_albums()`: Adjust the duplicate prevention window (default: 30 days)

## Automation

Consider scheduling this script to run daily using:
- **Windows**: Task Scheduler
- **Linux/Mac**: cron jobs
- **Cloud**: GitHub Actions, AWS Lambda, etc.

## License

This project is open source and available for personal and educational use.