import sys
import logging
from pathlib import Path

# Add the 'src' directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from src.app.main import main_streamlit_app
from src import config # Import config from src

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(Path(__file__).resolve().parent / "logs" / "application.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    """
    Entry point for the Streamlit RAG application.
    
    This script performs two key actions:
    1. It validates that all necessary environment variables are loaded via config.
    2. It launches the main Streamlit application function.
    """
    logger.info("Starting Streamlit RAG application...")
    # Ensure log directory exists
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Check for environment variables before launching the app
        config.check_environment_variables()
    except ValueError as e:
        logger.error(f"Failed to start application due to configuration error: {e}")
        # In a Streamlit app, we can use st.error even before st.set_page_config fully loads
        # but for a cleaner startup, we log and exit the script.
        # Streamlit itself might show an error if it fails to start.
        sys.exit(1)
    else:
        # If all is well, run the main application
        main_streamlit_app()
        logger.info("Streamlit RAG application finished.")