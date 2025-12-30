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
        """Recupere les equipes africaines principales"""
        logger.info("Collecte equipes africaines depuis Transfermarkt...")

        # Liste des equipes qualifiees CAN 2025 
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

            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status() # Check for HTTP errors
                
                # We are initializing BS4, but in this snippet we aren't doing deep parsing
                # In a full version, you would parse soup.find(...) here
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extraire valeur marchande (exemple simplifie)
                team_info = {
                    "name": team['name'],
                    "url": url,
                    "data_collected": "basic_info"
                }

                teams_data.append(team_info)
                logger.info(f"{team['name']} collectee")

                # Rate limiting (important for Transfermarkt to avoid blocking)
                time.sleep(2)

            except Exception as e:
                logger.error(f"Erreur pour {team['name']}: {e}")

        # Sauvegarder
        filepath = os.path.join(self.output_dir, "african_teams.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(teams_data, f, ensure_ascii=False, indent=2)

        logger.info(f"{len(teams_data)} equipes sauvegardees: {filepath}")
        return teams_data

    def get_top_players(self):
        """Recupere les meilleurs joueurs africains"""
        logger.info("Collecte top joueurs africains...")
        
        url = "https://www.transfermarkt.com/spieler-statistik/wertvollstespieler/marktwertetop/plus/0/galerie/0?ausrichtung=alle&spielerposition_id=alle&altersklasse=alle&jahrgang=0&land_id=0&kontinent_id=1&yt0=Show"
        
        players_data = []
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            rows = soup.select("table.items > tbody > tr")
            
            for row in rows[:25]: # Limiting to top 25 for this example
                name = row.select_one('td.hauptlink a').get_text(strip=True)
                position = row.select_one('td.zentriert').get_text(strip=True)
                team_img = row.select_one('td.zentriert a img')
                team = team_img['title'] if team_img else "N/A"
                
                players_data.append({"name": name, "position": position, "team": team})
                
            filepath = os.path.join(self.output_dir, "top_players.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(players_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Joueurs sauvegardes: {filepath}")
            return players_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des joueurs: {e}")
            return None

    def create_rag_documents(self):
        """Cree des documents RAG a partir des donnees Transfermarkt"""
        logger.info("Creation documents RAG Transfermarkt...")

        teams_path = os.path.join(self.output_dir, "african_teams.json")
        players_path = os.path.join(self.output_dir, "top_players.json")
        
        # Check if files exist
        if not os.path.exists(teams_path) or not os.path.exists(players_path):
            logger.error("Fichiers sources manquants (equipes ou joueurs).")
            return None

        with open(teams_path, 'r', encoding='utf-8') as f:
            teams = json.load(f)

        with open(players_path, 'r', encoding='utf-8') as f:
            players = json.load(f)

        rag_text = "EQUIPES ET JOUEURS CAN 2025\n\n"
        rag_text += "EQUIPES QUALIFIEES:\n"
        for team in teams:
            rag_text += f"- {team['name']}\n"

        rag_text += "\n\nTOP JOUEURS AFRICAINS:\n"
        for player in players:
            rag_text += f"- {player['name']} ({player['team']}) - {player['position']}\n"

        output_path = "data/processed/transfermarkt_teams_players.txt"
        os.makedirs("data/processed", exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rag_text)

        logger.info(f"Document RAG cree: {output_path}")
        return output_path

if __name__ == "__main__":
    bot = TransfermarktCAN()
    bot.get_african_teams()
    bot.get_top_players()
    bot.create_rag_documents()