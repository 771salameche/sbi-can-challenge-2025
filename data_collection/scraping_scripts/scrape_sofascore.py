import asyncio
import json
import os
import logging
from datetime import datetime
from sofascore_wrapper.api import SofascoreAPI
from sofascore_wrapper.search import Search

logger = logging.getLogger(__name__)

class SofaScoreCAN:
    def __init__(self, output_dir="data/raw/sofascore"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.scraper = SofascoreAPI()
        self.search_client = Search(self.scraper, search_string=None)

    async def _get_tournament_id(self, tournament_name: str):
        logger.info(f"Searching for tournament: {tournament_name}...")
        search_results = await self.search_client.search_all(search_string=tournament_name)
        logger.info(f"Full search results for '{tournament_name}': {json.dumps(search_results, indent=2)}")
        
        tournament_id = None
        for result in search_results.get('results', []):
            logger.info(f"Processing search result entity: {json.dumps(result.get('entity', {}), indent=2)}")
            if result.get('entityType') == 'tournament' and result.get('entity', {}).get('name') == tournament_name:
                tournament_id = result['entity']['id']
                logger.info(f"Found tournament '{tournament_name}' with ID: {tournament_id}")
                break
        if not tournament_id:
            logger.warning(f"Tournament '{tournament_name}' not found in search results.")
        return tournament_id

    async def get_can_tournament_info(self):
        logger.info("SofaScoreCAN.get_can_tournament_info called")
        
        try:
            tournament_id = await self._get_tournament_id("Africa Cup of Nations")
            if not tournament_id:
                logger.error("Could not find 'Africa Cup of Nations' tournament ID.")
                return None

            tournament_info = await self.scraper.get_tournament_details(tournament_id)

            filepath = os.path.join(self.output_dir, "can_tournament_info.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(tournament_info, f, ensure_ascii=False, indent=2)

            logger.info(f"Tournament info saved: {filepath}")
            return tournament_info
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des infos du tournoi: {e}")
            return None

    async def get_upcoming_matches(self):
        logger.info("SofaScoreCAN.get_upcoming_matches called")

        try:
            tournament_id = await self._get_tournament_id("Africa Cup of Nations")
            if not tournament_id:
                logger.error("Could not find 'Africa Cup of Nations' tournament ID.")
                return None

            # Assuming the API has a method to get events for a specific year
            # The example showed get_tournament_events(tournament_id), let's try that.
            matches = await self.scraper.get_tournament_events(tournament_id)

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
        if tournament:
            rag_text += f"Tournament: {tournament.get('name', 'N/A')}\n\n"

        rag_text += "UPCOMING MATCHES:\n"
        if matches:
            for match in matches:
                rag_text += f"- {match.get('homeTeam', {}).get('name', 'N/A')} vs {match.get('awayTeam', {}).get('name', 'N/A')} on {datetime.fromtimestamp(match.get('startTimestamp', 0)).strftime('%Y-%m-%d %H:%M') if match.get('startTimestamp') else 'N/A'}\n"
        else:
            rag_text += "No upcoming matches found.\n"
        
        output_path = "data/processed/sofascore_can_context.txt"
        os.makedirs("data/processed", exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rag_text)

        logger.info(f"RAG document created: {output_path}")
        return output_path
