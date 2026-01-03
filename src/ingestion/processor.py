import os
import re
import json
import logging
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

# Initialize logger
logger = logging.getLogger(__name__)

# --- Utility and Cleaning Functions (from clean_and_structure_data.py) ---
def clean_text_from_html(html_content: str) -> str:
    """Extracts and cleans text from HTML content using BeautifulSoup."""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    return text

def clean_rag_document(text: str) -> str:
    """Cleans a RAG document by removing URLs, social media artifacts, and extra whitespace."""
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'pic\.twitter\.com/\w+', '', text)
    text = re.sub(r'View this post on Instagram', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

# --- Le360 Article Processing (from process_le360_articles.py) ---
def process_le360_articles_json_to_rag(input_filepath: Path, output_filepath: Path):
    """
    Reads Le360 articles from a JSON file, formats them into a RAG-friendly
    text document, and saves the output.
    """
    logger.info(f"Processing Le360 articles from {input_filepath} to RAG format...")
    if not input_filepath.exists():
        logger.error(f"Input file not found: {input_filepath}")
        return

    with open(input_filepath, 'r', encoding='utf-8') as infile:
        articles = json.load(infile)
    
    output_filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(output_filepath, 'w', encoding='utf-8') as outfile:
        for article in articles:
            title = article.get('title', 'No Title')
            content = article.get('content', 'No Content')
            url = article.get('url', 'No URL')

            rag_entry = f"Titre de l'article: {title}\n" \
                        f"URL: {url}\n" \
                        f"Contenu:\n{content}\n\n" \
                        f"{'-'*80}\n\n"
            outfile.write(rag_entry)
    logger.info(f"Le360 RAG document created at: {output_filepath}")

# --- Le360 Details Extraction (from extract_le360_details.py) ---
def extract_can_details_from_le360_json_string(json_string: str) -> str:
    """
    Extracts structured CAN 2025 details (groups, schedule, stadiums) from a JSON string
    (presumably from le360.ma) and formats it into a RAG document.
    """
    try:
        json_data = json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError during Le360 details extraction: {e}")
        return None

    content_elements = json_data.get("content_elements", [])
    
    general_info = []
    groups = {}
    matches_schedule = []
    stadiums = set()
    
    parsing_groups_section = False
    parsing_matches_section = False

    for element in content_elements:
        content_type = element.get("type")
        content_text = element.get("content", "").strip()

        if content_type == "text":
            if "Groupes de la CAN 2025 au Maroc" in content_text:
                parsing_groups_section = True
                parsing_matches_section = False
                general_info.append(content_text)
                continue
            elif "Programme des matches – Phase de groupes de la CAN 2025" in content_text:
                parsing_matches_section = True
                parsing_groups_section = False
                general_info.append(content_text)
                continue
            elif "Phase à élimination directe" in content_text:
                parsing_matches_section = True
                parsing_groups_section = False
                general_info.append(content_text)
                continue
            
            if not parsing_groups_section and not parsing_matches_section and content_text:
                general_info.append(content_text)
            
            if parsing_groups_section:
                if content_text.startswith("A:") or \
                   content_text.startswith("B:") or \
                   content_text.startswith("C:") or \
                   content_text.startswith("D:") or \
                   content_text.startswith("E:") or \
                   content_text.startswith("F:"):
                    group_name = content_text[0]
                    teams = [team.strip() for team in content_text[2:].split(',')]
                    groups[group_name] = teams
            
            if parsing_matches_section:
                if ("décembre 2025" in content_text or "janvier 2026" in content_text) and \
                   ("h, au Stade" in content_text or "h, au Grand Stade" in content_text or "h, au Stade El Barid" in content_text):
                    matches_schedule.append(content_text)
                    
                    if "Stade" in content_text:
                        parts = content_text.split(" au ")
                        if len(parts) > 1:
                            stadium_part = parts[1]
                            stadium_full_name = stadium_part.split(" (Groupe")[0].split(".")[0].strip()
                            stadiums.add(stadium_full_name)
        
        elif content_type == "raw_html":
            html_content = element.get("content", "")
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if not groups:
                group_cards = soup.find_all(class_='group-card')
                for card in group_cards:
                    group_badge = card.find(class_='group-badge')
                    if group_badge:
                        group_name = group_badge.text.strip()
                        team_items = card.find_all(class_='team-item')
                        team_list = [item.text.strip() for item in team_items]
                        groups[group_name] = team_list
    
    rag_document_content = []
    rag_document_content.append("Détails complets de la Coupe d'Afrique des Nations 2025 (CAN 2025)\n\n")
    rag_document_content.append("--- Informations Générales ---")
    for info in general_info:
        rag_document_content.append(f"{info}\n")
    rag_document_content.append("\n")

    rag_document_content.append("--- Composition des Groupes ---")
    if groups:
        for group, team_list in sorted(groups.items()):
            rag_document_content.append(f"  Groupe {group}: {', '.join(team_list)}\n")
    else:
        rag_document_content.append("  Aucune information de groupe détaillée trouvée.\n")
    rag_document_content.append("\n")

    rag_document_content.append("--- Calendrier des Matchs ---")
    if matches_schedule:
        for match_info in matches_schedule:
            rag_document_content.append(f"- {match_info}\n")
    else:
        rag_document_content.append("  Aucun calendrier de match détaillé trouvé.\n")
    rag_document_content.append("\n")

    rag_document_content.append("--- Stades Hôtes ---")
    if stadiums:
        for stadium in sorted(list(stadiums)):
            rag_document_content.append(f"- {stadium}\n")
    else:
        rag_document_content.append("  Aucune information sur les stades trouvée dans le calendrier des matchs.\n")
    rag_document_content.append("\n")

    return "".join(rag_document_content)

def process_le360_details(input_json_filepath: Path, output_filepath: Path):
    """
    Loads a JSON file (e.g., from Le360 detailing CAN 2025 information),
    extracts structured details, and saves them as a RAG-ready text file.
    """
    logger.info(f"Extracting Le360 CAN details from {input_json_filepath}...")
    if not input_json_filepath.exists():
        logger.error(f"Input JSON file not found: {input_json_filepath}")
        return

    with open(input_json_filepath, 'r', encoding='utf-8') as f:
        json_content_from_file = f.read()

    rag_document = extract_can_details_from_le360_json_string(json_content_from_file)
    
    if rag_document:
        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(rag_document)
        logger.info(f"Le360 CAN 2025 details RAG document created at {output_filepath}")
    else:
        logger.warning(f"Failed to create Le360 CAN 2025 details RAG document from {input_json_filepath}")

# --- Data Merging and Deduplication (from merge_and_deduplicate_data.py) ---
def merge_and_deduplicate_rag_corpus(input_filepath: Path, output_filepath: Path):
    """
    Merges content from various RAG documents (separated by '--- Contenu de')
    and deduplicates lines.
    """
    logger.info(f"Merging and deduplicating RAG corpus from {input_filepath}...")
    if not input_filepath.exists():
        logger.error(f"Input file not found: {input_filepath}")
        return

    with open(input_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = content.split('--- Contenu de')
    
    unique_lines = set() # To help with deduplication across all sections
    merged_content = []

    for section in sections:
        if not section.strip():
            continue
            
        lines = section.split('\n')
        filename_header = lines[0]
        section_content = "\n".join(lines[1:])
        
        unique_section_lines = []
        for line in section_content.split('\n'):
            stripped_line = line.strip()
            if stripped_line and stripped_line not in unique_lines:
                unique_section_lines.append(line)
                unique_lines.add(stripped_line)
        
        if unique_section_lines:
            merged_content.append(f"--- Contenu de{filename_header}\n" + "\n".join(unique_section_lines) + "\n\n")

    output_filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write("".join(merged_content))
    logger.info(f"Merged and deduplicated RAG corpus created at: {output_filepath}")

# --- Squad List Appending (from append_squad_list.py) ---
def append_squad_list_to_file(filepath: Path, squad_list_content: str):
    """Appends additional squad list content to an existing file."""
    logger.info(f"Appending squad list to {filepath}...")
    if not filepath.exists():
        logger.warning(f"File not found for appending squad list: {filepath}. Creating new file.")
        existing_content = ""
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_content = f.read()

    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(existing_content + squad_list_content)
    logger.info(f"Squad list appended to {filepath}")


# --- Master RAG Document Creation (from create_master_rag_document.py) ---
def create_master_rag_document(processed_data_dir: Path, output_filepath: Path):
    """
    Consolidates and cleans various processed text files into a single master RAG document.
    """
    logger.info(f"Creating master RAG document from {processed_data_dir}...")
    if not processed_data_dir.exists():
        logger.error(f"Processed data directory not found: {processed_data_dir}")
        return

    all_cleaned_content = []
    seen_content = set() # To help with simple deduplication across files

    for filename in os.listdir(processed_data_dir):
        input_filepath = processed_data_dir / filename
        
        if input_filepath.suffix == ".txt":
            with open(input_filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            cleaned_content = clean_rag_document(content) # Use the generic cleaner
            
            if cleaned_content and cleaned_content not in seen_content:
                all_cleaned_content.append(f"--- Contenu de {filename} ---\n{cleaned_content}\n\n")
                seen_content.add(cleaned_content)
        else:
            logger.debug(f"Skipping non-text file: {filename} in processed data directory.")

    output_filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(output_filepath, 'w', encoding='utf-8') as outfile:
        outfile.write("".join(all_cleaned_content))
    logger.info(f"Master RAG document created at: {output_filepath}")
