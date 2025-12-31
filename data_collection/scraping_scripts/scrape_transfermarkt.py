import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TransfermarktCAN:
    """Scraping de donnees Transfermarkt"""

    def __init__(self, output_dir="data/raw/transfermarkt"):
        self.base_url = "https://www.transfermarkt.com"
        # Transfermarkt blocks requests without a browser-like User-Agent
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def get_african_teams(self):
        """Recupere les equipes africaines principales et leurs joueurs"""
        logger.info("Collecte equipes africaines et leurs joueurs depuis Transfermarkt...")

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
            logger.info(f"Collecte {team['name']}...")
            url = self.base_url + team['url_suffix']
            players = []
            
            for attempt in range(3):
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
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
                    logger.info(f"{team['name']} collectee avec {len(players)} joueurs.")
                    time.sleep(2)
                    break # Break the loop if successful
                except Exception as e:
                    logger.error(f"Erreur pour {team['name']} (attempt {attempt + 1}/3): {e}")
                    if attempt < 2:
                        logger.info("Retrying in 5 seconds...")
                        time.sleep(5)
                    else:
                        logger.error(f"Echec de la collecte pour {team['name']} apres 3 tentatives.")


        filepath = os.path.join(self.output_dir, "african_teams_with_players.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(teams_data, f, ensure_ascii=False, indent=2)

        logger.info(f"{len(teams_data)} equipes sauvegardees: {filepath}")
        return teams_data

    def create_rag_documents(self):
        """Cree des documents RAG a partir des donnees Transfermarkt"""
        logger.info("Creation documents RAG Transfermarkt...")

        teams_path = os.path.join(self.output_dir, "african_teams_with_players.json")
        
        if not os.path.exists(teams_path):
            logger.error("Fichier source manquant (equipes avec joueurs).")
            return None

        with open(teams_path, 'r', encoding='utf-8') as f:
            teams = json.load(f)

        rag_text = "EQUIPES ET JOUEURS CAN 2025\n\n"
        for team in teams:
            rag_text += f"EQUIPE: {team['name']}\n"
            rag_text += "JOUEURS:\n"
            for player in team.get('players', []):
                rag_text += f"- {player['name']} ({player['position']})\n"
            rag_text += "\n"

        output_path = "data/processed/transfermarkt_teams_players.txt"
        os.makedirs("data/processed", exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rag_text)

        logger.info(f"Document RAG cree: {output_path}")
        return output_path

if __name__ == "__main__":
    bot = TransfermarktCAN()
    bot.get_african_teams()
    bot.create_rag_documents()