import os
import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://sport.le360.ma"
CAN_PAGE = "https://sport.le360.ma/football/can/"

headers = {"User-Agent": "Mozilla/5.0"}

# dossier de sortie
output_dir = "CAN_Data/le360_articles"
os.makedirs(output_dir, exist_ok=True)

# 1) récupérer les liens des articles CAN
resp = requests.get(CAN_PAGE, headers=headers)
soup = BeautifulSoup(resp.text, "html.parser")

# extraire les liens relatifs vers les articles
links = set()
for a in soup.find_all("a", href=True):
    href = a["href"]
    # filtrer pour garder seulement les articles de CAN 2025
    if "/football/can/" in href or "/football/" in href:
        if href.startswith("/"):
            links.add(BASE_URL + href)

print(f"{len(links)} liens trouvés")

# 2) télécharger chaque article
for i, link in enumerate(links):
    try:
        r = requests.get(link, headers=headers)
        article_soup = BeautifulSoup(r.text, "html.parser")

        # titre et texte principal
        title_tag = article_soup.find("h1")
        if title_tag:
            title = title_tag.text.strip()
        else:
            title = "article_" + str(i)

        paragraphs = article_soup.find_all("p")
        text = "\n".join([p.get_text() for p in paragraphs])

        filename = title.replace(" ", "_").replace("/", "_") + ".txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n{text}")

        print(f"✔ [{i+1}] {title}")

        time.sleep(1)

    except Exception as e:
        print("❌ erreur:", e)
