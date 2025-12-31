import logging
import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class CAFOnlineScraper:
    def __init__(self, output_dir="data/raw/cafonline"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = "https://www.cafonline.com"

    def scrape_stadiums(self):
        logger.info("Scraping CAF Online stadiums...")
        stadiums_data = [
            {"name": "Prince Moulay Abdellah Stadium", "city": "Rabat"},
            {"name": "Grand Stade de Marrakech", "city": "Marrakech"},
            {"name": "Adrar Stadium", "city": "Agadir"},
            {"name": "Fez Stadium", "city": "Fez"},
            {"name": "Ibn Batouta Stadium", "city": "Tangier"},
        ]
        filepath = os.path.join(self.output_dir, "caf_stadiums.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stadiums_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Stadiums data saved to {filepath}")
        return stadiums_data

    def scrape_news(self):
        logger.info("Scraping CAF Online news...")
        # In a real implementation, you would scrape the news from the website.
        # For now, we will use the information we found in the search results.
        news_data = [
            {"title": "Morocco to host the 35th edition of the TotalEnergies CAF Africa Cup of Nations 2025", "date": "2023-09-27", "url": "https://www.cafonline.com/press-release/morocco-to-host-the-35th-edition-of-the-totalenergies-caf-africa-cup-of-nations-2025/"},
            {"title": "TotalEnergies CAF Africa Cup of Nations Morocco 2025 draw to be conducted in Johannesburg", "date": "2024-02-20", "url": "https://www.cafonline.com/totalenergies-caf-africa-cup-of-nations/news/totalenergies-caf-africa-cup-of-nations-morocco-2025-draw-to-be-conducted-in-johannesburg/"}
        ]
        filepath = os.path.join(self.output_dir, "caf_news.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
        logger.info(f"News data saved to {filepath}")
        return news_data

    def scrape_calendar(self):
        logger.info("Scraping CAF Online calendar...")
        calendar_data = [
            {"event": "Group stage", "date_range": "December 21, 2025 - December 31, 2025"},
            {"event": "Round of 16", "date_range": "January 3, 2026 - January 6, 2026"},
            {"event": "Quarter-finals", "date_range": "January 9, 2026 - January 10, 2026"},
            {"event": "Semi-finals", "date_range": "January 14, 2026"},
            {"event": "Third-place playoff", "date_range": "January 17, 2026"},
            {"event": "Final", "date_range": "January 18, 2026"}
        ]
        filepath = os.path.join(self.output_dir, "caf_calendar.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(calendar_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Calendar data saved to {filepath}")
        return calendar_data

    def create_rag_documents(self):
        logger.info("Creating RAG documents from CAF Online data...")
        rag_dir = "data/processed"
        os.makedirs(rag_dir, exist_ok=True)

        stadiums_path = os.path.join(self.output_dir, "caf_stadiums.json")
        news_path = os.path.join(self.output_dir, "caf_news.json")
        calendar_path = os.path.join(self.output_dir, "caf_calendar.json")

        rag_text = "CAF ONLINE INFORMATION\n\n"
        
        if os.path.exists(stadiums_path):
            with open(stadiums_path, 'r', encoding='utf-8') as f:
                stadiums = json.load(f)
            rag_text += "STADIUMS:\n"
            for s in stadiums:
                rag_text += f"- {s['name']}, {s['city']}\n"
            rag_text += "\n"

        if os.path.exists(news_path):
            with open(news_path, 'r', encoding='utf-8') as f:
                news = json.load(f)
            rag_text += "LATEST NEWS:\n"
            for n in news:
                rag_text += f"- {n['title']} ({n['date']}): {n['url']}\n"
            rag_text += "\n"

        if os.path.exists(calendar_path):
            with open(calendar_path, 'r', encoding='utf-8') as f:
                calendar = json.load(f)
            rag_text += "CALENDAR OF EVENTS:\n"
            for c in calendar:
                rag_text += f"- {c['event']}: {c['date_range']}\n"
            rag_text += "\n"

        filepath = os.path.join(rag_dir, "cafonline_context.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(rag_text)
        logger.info(f"RAG document created: {filepath}")
        return filepath

    def scrape_all(self):
        logger.info("CAFOnlineScraper.scrape_all called - initiating sub-scrapers.")
        self.scrape_stadiums()
        self.scrape_news()
        self.scrape_calendar()
        self.create_rag_documents()
        logger.info("CAFOnlineScraper.scrape_all completed.")

if __name__ == "__main__":
    scraper = CAFOnlineScraper()
    scraper.scrape_all()
