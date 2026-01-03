import logging
import sys
from pathlib import Path

# Add the 'src' directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from src.ingestion import loader
from src import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(Path(__file__).resolve().parent / "logs" / "ingestion.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to run the data ingestion pipeline.
    This script loads documents directly from the 'data/corpus' directory,
    creates embeddings, and stores them in the ChromaDB vector store.
    """
    logger.info("Starting the simplified data ingestion pipeline...")

    # Ensure all necessary environment variables are set before starting.
    try:
        config.check_environment_variables()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1) # Exit if configuration is missing

    # Ensure log directory exists
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # --- Ingest into Vector Store ---
    logger.info(f"Loading documents from '{config.CORPUS_PATH}' and ingesting into the vector store...")
    loader.ingest_pipeline()
    logger.info("Vector store ingestion complete.")

    logger.info("Data ingestion pipeline finished successfully!")

if __name__ == "__main__":
    main()
