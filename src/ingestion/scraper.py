import requests
from bs4 import BeautifulSoup
import logging
import os
import re
import json
import html
import time
import pandas as pd
import wikipedia
from datetime import datetime
from pathlib import Path

# Initialize logger
logger = logging.getLogger(__name__)

# --- Utility Functions (moved from scrape_le360_can_articles.py) ---
def remove_emojis(text: str) -> str:
    """Removes emojis from a string."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
        "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed Characters
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U000025AA-\U000025AB"  # White and black square, small
        "\U00002B05-\U00002B07"  # Arrows
        "\U00002934-\U00002935"  # Curly Loop
        "\U00002B50"             # White medium star
        "\U0000FE0F"             # Variation Selector
        "\U0000200D"             # Zero Width Joiner
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def clean_article_text(text: str) -> str:
    """Cleans article text by unescaping HTML entities and removing social media artifacts."""
    text = html.unescape(text)
    text = re.sub(r'pic.twitter.com/\w+', '', text)
    text = re.sub(r'View this post on Instagram', '', text, flags=re.IGNORECASE)
    text = re.sub(r'#[a-zA-Z0-9_]+', '', text)
    text = re.sub(r'@[a-zA-Z0-9_]+', '', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

# --- Le360 Scraper Functions (adapted from scrape_le360_can_articles.py) ---
def _get_le360_article_links(main_url: str) -> list:
    """Fetches article links from the main CAN page."""
    links = []
    try:
        response = requests.get(main_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for a_tag in soup.find_all('a', href=re.compile(r'/football/can/.*')):
            link = a_tag['href']
            if not link.startswith('http'):
                link = f"https://sport.le360.ma{link}"
            links.append(link)
        links = list(set(links))
        logger.info(f"Found {len(links)} unique Le360 article links.")
        return links
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching the main Le360 page: {e}")
        return []

def _scrape_le360_single_article(url: str) -> dict:
    """Scrapes the title and content of a single Le360 article."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "No Title Found"
        title = remove_emojis(clean_article_text(title))
        
        article_text = ""
        content_container = soup.find('article') or soup.find('div', class_='article-body') or soup.find('div', class_='main-content')
        if content_container:
            article_text = content_container.get_text(separator='\n', strip=True)
        else:
             article_text = "No content found."

        article_text = remove_emojis(clean_article_text(article_text))
        
        return {
            "url": url,
            "title": title,
            "content": article_text,
            "source": "le360.ma"
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping Le360 article at {url}: {e}")
        return None

def scrape_le360(main_url: str, output_filepath: Path):
    """Orchestrates scraping Le360 CAN articles and saves them to a JSON file."""
    logger.info(f"Starting scraper for Le360 CAN articles from {main_url}")
    
    article_links = _get_le360_article_links(main_url)
    scraped_articles = []
    
    if article_links:
        for link in article_links: 
            logger.info(f"Scraping Le360 article: {link}")
            article_data = _scrape_le360_single_article(link)
            if article_data:
                scraped_articles.append(article_data)

        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(scraped_articles, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Scraped data for {len(scraped_articles)} Le360 articles saved to {output_filepath}")
    else:
        logger.warning("No Le360 article links found. Exiting Le360 scraping.")

# --- SofaScore Scraper Functions (adapted from scrape_sofascore.py) ---
def scrape_sofascore(output_dir: Path):
    """Collects SofaScore data via an unofficial API."""
    logger.info("Collecting CAN tournament info from SofaScore...")

    base_url = "https://api.sofascore.com/api/v1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
    }
    output_dir.mkdir(parents=True, exist_ok=True)

    tournament_id = 270  # Africa Cup of Nations

    # Get tournament info
    try:
        url = f"{base_url}/unique-tournament/{tournament_id}/season/current/standings/total"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        filepath = output_dir / "sofascore_tournament_info.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"SofaScore tournament info saved: {filepath}")
    except Exception as e:
        logger.error(f"Error collecting SofaScore tournament info: {e}")

    # Get upcoming matches (example data as API is unofficial)
    logger.info("Collecting SofaScore CAN match calendar...")
    matches_data = {
        "matches": [
            {
                "date": "2025-01-13",
                "home_team": "Maroc",
                "away_team": "Tanzanie",
                "competition": "CAN 2025 - Phase de groupes"
            },
            {
                "date": "2025-01-13",
                "home_team": "RD Congo",
                "away_team": "Zambie",
                "competition": "CAN 2025 - Phase de groupes"
            }
        ],
        "collected_at": datetime.now().isoformat()
    }
    filepath = output_dir / "sofascore_upcoming_matches.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(matches_data, f, ensure_ascii=False, indent=2)
    logger.info(f"SofaScore match calendar saved: {filepath}")

# --- Transfermarkt Scraper Functions (adapted from scrape_transfermarkt.py) ---
def scrape_transfermarkt(output_dir: Path):
    """Scrapes Transfermarkt for African teams and their players."""
    logger.info("Collecting African teams and their players from Transfermarkt...")

    base_url = "https://www.transfermarkt.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    output_dir.mkdir(parents=True, exist_ok=True)

    teams = [
        {"name": "Morocco", "url_suffix": "/marokko/startseite/verein/3575"},
        {"name": "Senegal", "url_suffix": "/senegal/startseite/verein/3499"},
        {"name": "Côte d'Ivoire", "url_suffix": "/elfenbeinkuste/startseite/verein/3591"},
        {"name": "Egypt", "url_suffix": "/agypten/startseite/verein/3672"},
        {"name": "Nigeria", "url_suffix": "/nigeria/startseite/verein/3444"},
        {"name": "Cameroon", "url_suffix": "/kamerun/startseite/verein/3434"},
        {"name": "Algeria", "url_suffix": "/algerien/startseite/verein/3614"},
        {"name": "Tunisia", "url_suffix": "/tunesien/startseite/verein/3670"},
        {"name": "South Africa", "url_suffix": "/sudafrika/startseite/verein/3806"},
        {"name": "Burkina Faso", "url_suffix": "/burkina-faso/startseite/verein/5872"},
        {"name": "Angola", "url_suffix": "/angola/startseite/verein/3585"},
        {"name": "Benin", "url_suffix": "/benin/startseite/verein/3955"},
        {"name": "Botswana", "url_suffix": "/botsuana/startseite/verein/15229"},
        {"name": "Comoros", "url_suffix": "/komoren/startseite/verein/16430"},
        {"name": "DR Congo", "url_suffix": "/demokratische-republik-kongo/startseite/verein/3854"},
        {"name": "Equatorial Guinea", "url_suffix": "/aquatorialguinea/startseite/verein/13485"},
        {"name": "Gabon", "url_suffix": "/gabun/startseite/verein/5704"},
        {"name": "Mali", "url_suffix": "/mali/startseite/verein/3674"},
        {"name": "Mozambique", "url_suffix": "/mosambik/startseite/verein/5129"},
        {"name": "Sudan", "url_suffix": "/sudan/startseite/verein/13313"},
        {"name": "Tanzania", "url_suffix": "/tansania/startseite/verein/14666"},
        {"name": "Uganda", "url_suffix": "/uganda/startseite/verein/13497"},
        {"name": "Zambia", "url_suffix": "/sambia/startseite/verein/3703"},
        {"name": "Zimbabwe", "url_suffix": "/simbabwe/startseite/verein/3583"},
    ]

    teams_data = []

    for team in teams:
        logger.info(f"Collecting {team['name']}...")
        url = base_url + team['url_suffix']
        players = []
        
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                player_rows = soup.select("table.items > tbody > tr")
                for row in player_rows:
                    name_element = row.select_one('td.hauptlink a')
                    if name_element:
                        name = name_element.get_text(strip=True)
                        position = row.select_one('td.zentriert').get_text(strip=True) if row.select_one('td.zentriert') else 'N/A'
                        players.append({"name": name, "position": position})

                team_info = {
                    "name": team['name'],
                    "url": url,
                    "players": players,
                    "data_collected": "basic_info_with_players"
                }
                teams_data.append(team_info)
                logger.info(f"{team['name']} collected with {len(players)} players.")
                time.sleep(2)
                break
            except Exception as e:
                logger.error(f"Error for {team['name']} (attempt {attempt + 1}/3): {e}")
                if attempt < 2:
                    logger.info("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    logger.error(f"Failed to collect for {team['name']} after 3 attempts.")

    filepath = output_dir / "transfermarkt_african_teams_with_players.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(teams_data, f, ensure_ascii=False, indent=2)
    logger.info(f"{len(teams_data)} teams saved: {filepath}")

# --- Wikipedia Scraper Functions (adapted from scrape_wikipedia.py) ---
def scrape_wikipedia(output_dir: Path):
    """Collects CAN data from Wikipedia."""
    logger.info("Starting Wikipedia CAN data collection...")

    wikipedia.set_lang('fr')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get CAN History
    logger.info("Collecting CAN history from Wikipedia...")
    try:
        page = wikipedia.page("Coupe_d'Afrique_des_nations_de_football")
        data = {
            "title": page.title,
            "summary": page.summary,
            "full_text": page.content,
            "url": page.url,
            "collected_at": datetime.now().isoformat()
        }
        filepath = output_dir / "wikipedia_can_history.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Wikipedia CAN history saved: {filepath}")
    except wikipedia.exceptions.PageError:
        logger.error("Wikipedia page for CAN history not found.")
    except Exception as e:
        logger.error(f"Error collecting Wikipedia CAN history: {e}")

    # Get CAN Editions
    logger.info("Collecting CAN editions from Wikipedia...")
    editions_data = []
    years = [
        1957, 1959, 1962, 1963, 1965, 1968,
        1970, 1972, 1974, 1976, 1978,
        1980, 1982, 1984, 1986, 1988,
        1990, 1992, 1994, 1996, 1998,
        2000, 2002, 2004, 2006, 2008,
        2010, 2012, 2013, 2015, 2017,
        2019, 2021, 2023, 2025 # Include 2025 as a potential future page
    ]
    for year in years:
        page_title = f"Coupe d'Afrique des nations de football {year}"
        try:
            page = wikipedia.page(page_title, auto_suggest=False)
            editions_data.append({
                "year": year,
                "title": page.title,
                "summary": page.summary,
                "full_text": page.content,
                "url": page.url
            })
            logger.info(f"Wikipedia Edition {year} collected.")
        except wikipedia.exceptions.PageError:
            logger.warning(f"Wikipedia page for year {year} not found.")
        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning(f"Wikipedia disambiguation page for year {year}: {e.options}")
        except Exception as e:
            logger.error(f"Error collecting Wikipedia edition {year}: {e}")

    filepath = output_dir / "wikipedia_can_editions.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(editions_data, f, ensure_ascii=False, indent=2)
    logger.info(f"{len(editions_data)} Wikipedia editions saved: {filepath}")
