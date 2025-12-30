import os
import logging
from datetime import datetime

from scraping_scripts.scrape_wikipedia import WikipediaCAN
from scraping_scripts.scrape_transfermarkt import TransfermarktCAN
from scraping_scripts.scrape_sofascore import SofaScoreCAN
from scraping_scripts.cafonline_scraper import CAFOnlineScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Orchestrateur principal de collecte de donnees"""
    logger.info("="*70)
    logger.info("COLLECTE DE DONNEES CAN 2025 - SBI STUDENT CHALLENGE")
    logger.info("="*70)
    
    # Create directory structure
    os.makedirs("data/raw/wikipedia", exist_ok=True)
    os.makedirs("data/raw/transfermarkt", exist_ok=True)
    os.makedirs("data/raw/sofascore", exist_ok=True)
    os.makedirs("data/raw/cafonline", exist_ok=True)  # Added this
    os.makedirs("data/processed", exist_ok=True)

    # ========== 1. WIKIPEDIA ==========
    logger.info("-" * 30)
    logger.info("1. COLLECTE WIKIPEDIA")
    logger.info("-" * 30)
    
    try:
        wiki_scraper = WikipediaCAN()
        wiki_scraper.get_can_history()
        wiki_scraper.get_can_editions()
        wiki_scraper.get_can_2025_info()
        wiki_scraper.create_rag_documents()
    except Exception as e:
        logger.error(f"Erreur lors de la collecte Wikipedia: {e}")

    # ========== 2. TRANSFERMARKT ==========
    logger.info("-" * 30)
    logger.info("2. COLLECTE TRANSFERMARKT")
    logger.info("-" * 30)
    
    try:
        tm_scraper = TransfermarktCAN()
        tm_scraper.get_african_teams()
        tm_scraper.get_top_players()
        tm_scraper.create_rag_documents()
    except Exception as e:
        logger.error(f"Erreur lors de la collecte Transfermarkt: {e}")

    # ========== 3. SOFASCORE ==========
    logger.info("-" * 30)
    logger.info("3. COLLECTE SOFASCORE")
    logger.info("-" * 30)
    
    try:
        sofascore_scraper = SofaScoreCAN()
        sofascore_scraper.get_can_tournament_info()
        sofascore_scraper.get_upcoming_matches()
        sofascore_scraper.create_rag_documents()
    except Exception as e:
        logger.error(f"Erreur lors de la collecte SofaScore: {e}")

    # ========== 4. CAF ONLINE (NEW) ==========
    logger.info("-" * 30)
    logger.info("4. COLLECTE CAF ONLINE (OFFICIEL)")
    logger.info("-" * 30)

    try:
        caf_scraper = CAFOnlineScraper()
        caf_scraper.scrape_all() # This method runs stadiums, news, calendar and RAG creation
    except Exception as e:
        logger.error(f"Erreur lors de la collecte CAF Online: {e}")

    # ========== RESUME ==========
    logger.info("="*70)
    logger.info("COLLECTE TERMINEE")
    logger.info("="*70)
    logger.info("Fichiers crees dans data/raw/ et data/processed/")

if __name__ == "__main__":
    main()