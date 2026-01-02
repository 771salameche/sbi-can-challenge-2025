import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
import re
import logging

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class CAFOnlineScraper:
    """Scraper pour le site officiel de la CAF - CAN 2025"""

    def __init__(self, output_dir="data/raw/cafonline"):
        self.base_url = "https://www.cafonline.com"
        # URLs fournies par l'utilisateur
        self.urls = {
            "news": "https://www.cafonline.com/fr/can2025/infos/",
            "calendar_results": "https://www.cafonline.com/fr/can2025/calendrier-resultats/",
            "stadiums": [
                "https://www.cafonline.com/fr/can2025/stadiums/moulay-el-hassan-stadium-rabat/",
                "https://www.cafonline.com/fr/can2025/stadiums/le-grand-stade-d-agadir/",
                "https://www.cafonline.com/fr/can2025/stadiums/grand-stade-de-tanger/",
                "https://www.cafonline.com/fr/can2025/stadiums/marrakech-stadium/",
                "https://www.cafonline.com/fr/can2025/stadiums/mohammed-v-stadium/",
                "https://www.cafonline.com/fr/can2025/stadiums/fez-stadium/",
                "https://www.cafonline.com/fr/can2025/stadiums/moulay-abdellah-stadium-rabat/",
                "https://www.cafonline.com/fr/can2025/stadiums/olympic-stadium-of-rabat/",
                "https://www.cafonline.com/fr/can2025/stadiums/el-barid-stadium/"
            ]
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.cafonline.com/'
        }
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.session = requests.Session()

    def get_page(self, url):
        """Récupère une page avec gestion d'erreur"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de {url}: {e}")
            return None

    # ========================================================================
    # 1. STADES (URLs Spécifiques)
    # ========================================================================

    def scrape_stadiums(self):
        """Visite chaque page de stade spécifique pour extraire les infos"""
        logger.info("🏟️ Extraction des stades via les pages dédiées...")
        
        stadiums_data = []
        
        for url in self.urls["stadiums"]:
            logger.info(f"  Visite: {url}")
            soup = self.get_page(url)
            
            if soup:
                stadium_info = self._parse_stadium_page(soup, url)
                if stadium_info:
                    stadiums_data.append(stadium_info)
            else:
                logger.warning(f"  Impossible d'accéder à {url}")
            
            # Pause pour être poli envers le serveur
            time.sleep(1)

        # Si échec total, utiliser défaut
        if not stadiums_data:
            logger.warning("Aucune donnée stade trouvée, utilisation des données par défaut.")
            stadiums_data = self._get_default_stadiums()

        # Sauvegarder
        filepath = os.path.join(self.output_dir, "stadiums.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stadiums_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ {len(stadiums_data)} stades sauvegardés: {filepath}")
        return stadiums_data

    def _parse_stadium_page(self, soup, url):
        """Extrait les détails d'une page individuelle de stade"""
        try:
            # Titre (Nom du stade)
            name_elem = soup.find('h1') or soup.find('h2', class_=re.compile('title|name', re.I))
            name = name_elem.get_text(strip=True) if name_elem else "Inconnu"
            
            # Essayer de trouver la ville et la capacité dans le texte
            # On cherche des blocs de texte contenant des mots clés
            text_content = soup.get_text(separator="\n")
            
            # Recherche regex simple pour la capacité (ex: "Capacité : 45 000")
            capacity_match = re.search(r'(?:capacité|capacity)\s*[:.]?\s*([\d\s,]+)', text_content, re.IGNORECASE)
            capacity = capacity_match.group(1).strip() if capacity_match else "Non spécifiée"
            
            # Recherche regex pour la ville (souvent mentionnée dans le titre ou les premiers paragraphes)
            # Ceci est une heuristique simple
            cities = ["Rabat", "Casablanca", "Tanger", "Agadir", "Marrakech", "Fès", "Fez"]
            found_city = "Maroc"
            for city in cities:
                if city.lower() in text_content.lower() or city.lower() in url.lower():
                    found_city = city
                    break
            
            return {
                "name": name,
                "city": found_city,
                "capacity": capacity,
                "url": url,
                "scraped_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur parsing page stade: {e}")
            return None

    def _get_default_stadiums(self):
        """Données par défaut (backup)"""
        return [
            {"name": "Complexe Prince Moulay Abdellah", "city": "Rabat", "capacity": "52 000"},
            {"name": "Grand Stade de Casablanca", "city": "Casablanca", "capacity": "93 000"},
            {"name": "Stade de Tanger", "city": "Tanger", "capacity": "65 000"},
            {"name": "Stade de Marrakech", "city": "Marrakech", "capacity": "45 240"},
            {"name": "Stade Adrar", "city": "Agadir", "capacity": "45 480"},
            {"name": "Stade de Fès", "city": "Fès", "capacity": "45 000"}
        ]

    # ========================================================================
    # 2. ACTUALITÉS (Page Infos)
    # ========================================================================

    def scrape_news(self, max_articles=15):
        """Extrait les actualités depuis la page Infos"""
        logger.info("📰 Extraction des actualités...")
        
        url = self.urls["news"]
        soup = self.get_page(url)

        if not soup:
            return []

        news_data = []
        # Sélecteurs génériques pour articles (cards, items)
        article_elements = soup.find_all(['article', 'div'], class_=re.compile('post|news-item|card|article', re.I))[:max_articles]

        for i, element in enumerate(article_elements, 1):
            article = self._parse_news_element(element)
            if article and article['title']: # S'assurer qu'on a au moins un titre
                news_data.append(article)
                logger.info(f"  ✓ Article: {article['title'][:40]}...")

        filepath = os.path.join(self.output_dir, "news.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ {len(news_data)} actualités sauvegardées: {filepath}")
        return news_data

    def _parse_news_element(self, element):
        try:
            title_elem = element.find(['h2', 'h3', 'h4', 'h5', 'a'], class_=re.compile('title', re.I))
            if not title_elem:
                # Fallback: chercher n'importe quel lien avec du texte significatif
                links = element.find_all('a')
                for l in links:
                    if l.get_text(strip=True) and len(l.get_text(strip=True)) > 10:
                        title_elem = l
                        break
            
            title = title_elem.get_text(strip=True) if title_elem else ""
            if not title: return None

            # Lien
            link_elem = element.find('a', href=True) if not element.name == 'a' else element
            link = link_elem['href'] if link_elem else ""
            if link and not link.startswith('http'):
                link = self.base_url + link

            # Date
            date_elem = element.find(['time', 'span'], class_=re.compile('date|time|meta', re.I))
            date = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y-%m-%d')

            return {
                "title": title,
                "link": link,
                "date": date,
                "scraped_at": datetime.now().isoformat()
            }
        except:
            return None

    # ========================================================================
    # 3. CALENDRIER ET CLASSEMENT (Page Unique)
    # ========================================================================

    def scrape_calendar_and_standings(self):
        """Extrait le calendrier et tente d'extraire le classement de la même page"""
        logger.info("📅 Extraction Calendrier & Résultats...")
        
        url = self.urls["calendar_results"]
        soup = self.get_page(url)
        
        if not soup:
            logger.warning("Impossible d'accéder à la page calendrier.")
            return [], {}

        # --- 1. Calendrier (Matchs) ---
        matches_data = []
        # On cherche des éléments qui ressemblent à des matchs (souvent listes ou tableaux)
        match_elements = soup.find_all(['div', 'tr'], class_=re.compile('match|fixture|row', re.I))
        
        for el in match_elements:
            # Filtre simple pour éviter les déchets : doit contenir deux équipes ou une heure
            text = el.get_text(strip=True)
            if len(text) > 10 and ("-" in text or "vs" in text or ":" in text):
                match = self._parse_match_element(el)
                if match:
                    matches_data.append(match)

        # Sauvegarde Calendrier
        cal_path = os.path.join(self.output_dir, "calendar.json")
        with open(cal_path, 'w', encoding='utf-8') as f:
            json.dump(matches_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ {len(matches_data)} matchs potentiels trouvés.")

        # --- 2. Classements (Standings) ---
        logger.info("🏆 Tentative d'extraction des classements (si non chargés dynamiquement)...")
        standings_data = {}
        
        # BeautifulSoup voit le HTML caché (display:none), donc on cherche tous les tableaux
        tables = soup.find_all('table')
        
        for i, table in enumerate(tables):
            # Heuristique: un tableau de classement a souvent "Pts", "G", "P" ou des chiffres
            headers = [th.get_text(strip=True).lower() for th in table.find_all(['th', 'td'])]
            if any(k in str(headers) for k in ['pts', 'j', 'pl', 'w', 'd', 'l']):
                group_name = f"Groupe {i+1}"
                # Essayer de trouver le nom du groupe juste avant le tableau
                prev_header = table.find_previous(['h2', 'h3', 'h4'])
                if prev_header:
                    group_name = prev_header.get_text(strip=True)
                
                rows = table.find_all('tr')[1:] # Skip header
                group_standings = []
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        group_standings.append({
                            "team": cols[0].get_text(strip=True) if cols else "N/A",
                            "points": cols[-1].get_text(strip=True) if cols else "0",
                            "details": [c.get_text(strip=True) for c in cols]
                        })
                
                if group_standings:
                    standings_data[group_name] = group_standings

        if not standings_data:
            logger.warning("⚠️ Aucun classement trouvé. Il est probable que les données nécessitent un clic (JavaScript).")
            logger.info("ℹ️ Pour les sites dynamiques (React/Angular/Tabs), 'requests' ne suffit pas.")
        else:
            logger.info(f"✅ Classements trouvés pour {len(standings_data)} groupes.")

        # Sauvegarde Classements
        stand_path = os.path.join(self.output_dir, "standings.json")
        with open(stand_path, 'w', encoding='utf-8') as f:
            json.dump(standings_data, f, ensure_ascii=False, indent=2)

        return matches_data, standings_data

    def _parse_match_element(self, element):
        """Parse générique d'une ligne de match"""
        try:
            # C'est une heuristique car la structure exacte change souvent
            text = element.get_text(" ", strip=True)
            # Essayer de trouver une date
            date_match = re.search(r'\d{1,2}\s+(?:jan|feb|mars|avr|mai|juin|juil|aout|sept|oct|nov|dec)[a-z]*\s+\d{4}', text, re.I)
            date = date_match.group(0) if date_match else "Date inconnue"
            
            # Nettoyer le texte pour garder l'essentiel
            return {
                "raw_text": text, # Garder le texte brut pour le RAG si le parsing échoue
                "date_extracted": date
            }
        except:
            return None

    # ========================================================================
    # 4. RAG GENERATION
    # ========================================================================

    def create_rag_documents(self):
        """Crée des documents texte consolidés"""
        logger.info("📝 Création documents RAG...")
        rag_dir = "data/processed"
        os.makedirs(rag_dir, exist_ok=True)
        
        files_created = []

        # 1. Stades
        try:
            with open(os.path.join(self.output_dir, "stadiums.json"), 'r', encoding='utf-8') as f:
                stadiums = json.load(f)
            
            txt = "GUIDE DES STADES CAN 2025\n\n"
            for s in stadiums:
                txt += f"🏟️ {s['name']} ({s['city']})\n"
                txt += f"   Capacité: {s['capacity']}\n"
                txt += f"   Source: {s.get('url', 'N/A')}\n\n"
            
            path = os.path.join(rag_dir, "caf_stadiums.txt")
            with open(path, 'w', encoding='utf-8') as f: f.write(txt)
            files_created.append(path)
        except Exception as e:
            logger.warning(f"Pas de données stades pour RAG: {e}")

        # 2. Infos/News
        try:
            with open(os.path.join(self.output_dir, "news.json"), 'r', encoding='utf-8') as f:
                news = json.load(f)
            
            txt = "DERNIÈRES ACTUALITÉS CAN 2025 (CAF OFFICIEL)\n\n"
            for n in news:
                txt += f"📰 {n['title']}\n   Date: {n['date']}\n   Lien: {n['link']}\n\n"
                
            path = os.path.join(rag_dir, "caf_news.txt")
            with open(path, 'w', encoding='utf-8') as f: f.write(txt)
            files_created.append(path)
        except: pass

        # 3. Calendrier/Classement
        try:
            with open(os.path.join(self.output_dir, "calendar.json"), 'r', encoding='utf-8') as f:
                matches = json.load(f)
            
            txt = "CALENDRIER CAN 2025\n\n"
            for m in matches[:30]:
                txt += f"Match: {m.get('raw_text', 'N/A')}\n"
            
            path = os.path.join(rag_dir, "caf_calendar.txt")
            with open(path, 'w', encoding='utf-8') as f: f.write(txt)
            files_created.append(path)
        except: pass

        logger.info(f"✅ Documents RAG créés: {files_created}")
        return files_created

    def scrape_all(self):
        self.scrape_stadiums()
        self.scrape_news()
        self.scrape_calendar_and_standings()
        self.create_rag_documents()

if __name__ == "__main__":
    bot = CAFOnlineScraper()
    bot.scrape_all()