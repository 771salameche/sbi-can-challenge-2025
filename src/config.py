import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# --- Project Root ---
# Establishes the project root directory.
# All other paths will be relative to this.
# Assuming this config.py is in src/, so PROJECT_ROOT is its parent.
PROJECT_ROOT = Path(__file__).parent.parent

# --- API Keys & Endpoints ---
# Fetches all required API keys and settings from environment variables.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

# --- Data Paths ---
# Defines the structured paths for data storage.
DATA_PATH = PROJECT_ROOT / "data"
CORPUS_PATH = DATA_PATH / "corpus"
RAW_DATA_PATH = DATA_PATH / "raw"
PROCESSED_DATA_PATH = DATA_PATH / "processed"

# --- Vector Store Path ---
# Defines the location for the persistent ChromaDB vector store.
CHROMA_DB_PATH = DATA_PATH / "chroma_db" # Changed from previous to match new architecture

# --- LLM & Embedding Model Parameters ---
# Centralizes model names and parameters for easy swapping and tuning.
EMBEDDING_MODEL_NAME = "text-embedding-ada-002" # Or your specific Azure deployment name
LLM_MODEL_NAME = "gemini-1.5-flash"

# --- Text Splitting Parameters ---
# Defines the parameters for document chunking.
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def check_environment_variables():
    """Checks if all required environment variables are set."""
    required_vars = [
        "GOOGLE_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"
    ]
    missing_vars = [var for var in required_vars if not globals().get(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}. Please check your .env file.")
    print("All required environment variables are loaded.")

