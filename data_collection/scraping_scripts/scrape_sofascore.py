import requests
import json
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class SofaScoreCAN:
    """Collecte de donnees SofaScore via API non-officielle"""

    def __init__(self, output_dir="data/raw/sofascore"):
        self.base_url = "https://api.sofascore.com/api/v1"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def get_can_tournament_info(self):
        """Recupere infos sur le tournoi CAN"""
        logger.info("Collecte infos tournoi CAN depuis SofaScore...")

        # ID du tournoi CAN 
        tournament_id = 270  # Africa Cup of Nations

        try:
            url = f"{self.base_url}/unique-tournament/{tournament_id}/season/current/standings/total"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()

                filepath = os.path.join(self.output_dir, "tournament_info.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)

                logger.info(f"Infos tournoi sauvegardees: {filepath}")
                return data
            else:
                logger.warning(f"Erreur API: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Erreur: {e}")
            return None

    def get_upcoming_matches(self):
        """Recupere le calendrier des matchs"""
        logger.info("Collecte calendrier matchs CAN...")

        # Donnees exemple (en production, utiliser vraie API)
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

        filepath = os.path.join(self.output_dir, "upcoming_matches.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(matches_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Calendrier sauvegarde: {filepath}")
        return matches_data

    def create_rag_documents(self):
        """Cree des documents RAG pour SofaScore"""
        logger.info("Creation documents RAG SofaScore...")

        matches_path = os.path.join(self.output_dir, "upcoming_matches.json")
        
        if not os.path.exists(matches_path):
            logger.error(f"Fichier introuvable: {matches_path}")
            return None
            
        with open(matches_path, 'r', encoding='utf-8') as f:
            matches = json.load(f)

        rag_text = "CALENDRIER CAN 2025\n\n"
        for match in matches['matches']:
            rag_text += f"{match['date']}: {match['home_team']} vs {match['away_team']}\n"

        output_path = "data/processed/sofascore_calendar.txt"
        os.makedirs("data/processed", exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rag_text)

        logger.info(f"Document RAG cree: {output_path}")
        return output_path

if __name__ == "__main__":
    bot = SofaScoreCAN()
    # Note: get_can_tournament_info might fail if the API endpoint or ID is outdated
    # as SofaScore's internal API changes frequently.
    bot.get_can_tournament_info()
    bot.get_upcoming_matches()
    bot.create_rag_documents()