import requests
from bs4 import BeautifulSoup
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SofaScoreCAN:
    def __init__(self, output_dir="data/raw/sofascore"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_can_tournament_info(self):
        logger.info("SofaScoreCAN.get_can_tournament_info called")
        
        url = "https://www.sofascore.com/tournament/football/africa/africa-cup-of-nations/19"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Africa Cup of Nations"

            tournament_info = {
                "name": title,
                "host": "Morocco", 
                "dates": "July 23, 2025 – August 21, 2025", 
                "teams": 24,
                "collected_at": datetime.now().isoformat()
            }

            filepath = os.path.join(self.output_dir, "can_tournament_info.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(tournament_info, f, ensure_ascii=False, indent=2)

            logger.info(f"Tournament info saved: {filepath}")
            return tournament_info
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des infos du tournoi: {e}")
            return None

    def get_upcoming_matches(self):
        logger.info("SofaScoreCAN.get_upcoming_matches called")

        url = "https://www.sofascore.com/tournament/football/africa/africa-cup-of-nations/19"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            matches = []
            
            match_elements = soup.select('div.list-wrapper a')
            
            for element in match_elements[:5]:
                home_team_element = element.select_one('div.team.home .name')
                away_team_element = element.select_one('div.team.away .name')
                
                if home_team_element and away_team_element:
                    home_team = home_team_element.get_text(strip=True)
                    away_team = away_team_element.get_text(strip=True)
                    match_date = element.select_one('div.status-or-time').get_text(strip=True)
                    
                    matches.append({
                        "match": f"{home_team} vs {away_team}",
                        "date": match_date
                    })

            filepath = os.path.join(self.output_dir, "upcoming_matches.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(matches, f, ensure_ascii=False, indent=2)

            logger.info(f"Upcoming matches saved: {filepath}")
            return matches
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des matchs: {e}")
            return None
        
    def create_rag_documents(self):
        logger.info("SofaScoreCAN.create_rag_documents called")

        tournament_path = os.path.join(self.output_dir, "can_tournament_info.json")
        matches_path = os.path.join(self.output_dir, "upcoming_matches.json")
        
        if not os.path.exists(tournament_path) or not os.path.exists(matches_path):
            logger.error("Source files for SofaScore are missing.")
            return None

        with open(tournament_path, 'r', encoding='utf-8') as f:
            tournament = json.load(f)

        with open(matches_path, 'r', encoding='utf-8') as f:
            matches = json.load(f)

        rag_text = f"SOFASCORE - CAN 2025\n\n"
        rag_text += f"Tournament: {tournament['name']}\nHost: {tournament['host']}\n\n"
        rag_text += "UPCOMING MATCHES:\n"
        if matches:
            for match in matches:
                rag_text += f"- {match['match']} on {match['date']}\n"
        else:
            rag_text += "No upcoming matches found.\n"
        
        output_path = "data/processed/sofascore_can_context.txt"
        os.makedirs("data/processed", exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rag_text)

        logger.info(f"RAG document created: {output_path}")
        return output_path