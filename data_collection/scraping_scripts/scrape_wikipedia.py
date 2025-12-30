import wikipedia
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

class WikipediaCAN:
    """Collecte de donnees CAN via l'API Wikipedia"""

    def __init__(self, output_dir="data/raw/wikipedia"):
        wikipedia.set_lang('fr')
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def get_can_history(self):
        """Recupere l'historique complet de la CAN"""
        logger.info("Collecte historique CAN depuis Wikipedia...")

        try:
            page = wikipedia.page("Coupe_d'Afrique_des_nations_de_football")
        except wikipedia.exceptions.PageError:
            logger.error("Page Wikipedia introuvable")
            return None

        data = {
            "title": page.title,
            "summary": page.summary,
            "full_text": page.content,
            "url": page.url,
            "collected_at": datetime.now().isoformat()
        }

        # Sauvegarder
        filepath = os.path.join(self.output_dir, "can_history.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Historique sauvegarde: {filepath}")
        return data

    def get_can_editions(self):
        """Liste des editions de la CAN"""
        logger.info("Collecte des editions CAN...")

        editions_data = []

        # Liste des annees CAN (recentes et historiques)
        years = [
    1957, 1959, 1962, 1963, 1965, 1968,
    1970, 1972, 1974, 1976, 1978,
    1980, 1982, 1984, 1986, 1988,
    1990, 1992, 1994, 1996, 1998,
    2000, 2002, 2004, 2006, 2008,
    2010, 2012, 2013, 2015, 2017,
    2019, 2021, 2023
]


        for year in years:
            page_title = f"Coupe_d'Afrique_des_nations_de_football_{year}"
            try:
                page = wikipedia.page(page_title)
                editions_data.append({
                    "year": year,
                    "title": page.title,
                    "summary": page.summary[:500],
                    "url": page.url
                })
                logger.info(f"Edition {year} collectee")
            except wikipedia.exceptions.PageError:
                logger.warning(f"Page pour l'annee {year} introuvable.")

        # Sauvegarder
        filepath = os.path.join(self.output_dir, "can_editions.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(editions_data, f, ensure_ascii=False, indent=2)

        logger.info(f"{len(editions_data)} editions sauvegardees: {filepath}")
        return editions_data

    def get_can_2025_info(self):
        """Informations sur la CAN 2025"""
        logger.info("Collecte infos CAN 2025...")

        try:
            page = wikipedia.page("Coupe_d'Afrique_des_nations_de_football_2025")
            data = {
                "title": page.title,
                "summary": page.summary,
                "full_text": page.content,
                "url": page.url,
                "collected_at": datetime.now().isoformat()
            }

            filepath = os.path.join(self.output_dir, "can_2025.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"CAN 2025 sauvegardee: {filepath}")
            return data
        except wikipedia.exceptions.PageError:
            logger.warning("Page CAN 2025 non disponible sur Wikipedia")
            return None

    def create_rag_documents(self):
        """Cree des documents texte optimises pour le RAG"""
        logger.info("Creation documents RAG...")

        rag_dir = "data/processed"
        os.makedirs(rag_dir, exist_ok=True)

        history_path = os.path.join(self.output_dir, "can_history.json")
        
        # Check if source file exists before trying to open
        if not os.path.exists(history_path):
            logger.error(f"Fichier source introuvable: {history_path}")
            return None

        # Charger les donnees collectees
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)

        # Creer document RAG
        rag_text = f"""HISTORIQUE DE LA COUPE D'AFRIQUE DES NATIONS
{history['summary']}

Source: {history['url']}
Derniere mise a jour: {history['collected_at']}

{history['full_text'][:5000]}"""

        filepath = os.path.join(rag_dir, "wikipedia_can_context.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(rag_text)

        logger.info(f"Document RAG cree: {filepath}")
        return filepath

# Example usage
if __name__ == "__main__":
    bot = WikipediaCAN()
    bot.get_can_history()
    bot.get_can_editions()
    bot.get_can_2025_info()
    bot.create_rag_documents()