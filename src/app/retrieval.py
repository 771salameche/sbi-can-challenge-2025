import logging
import streamlit as st
from langchain_chroma import Chroma
from src import config
from src.app.llm_services import get_azure_openai_embeddings_model

logger = logging.getLogger(__name__)

@st.cache_resource
def get_vector_store():
    """Initializes and returns the ChromaDB vector store."""
    logger.info(f"Attempting to load ChromaDB from {config.CHROMA_DB_PATH}...")
    try:
        embeddings = get_azure_openai_embeddings_model()
        if embeddings is None:
            st.error("Embeddings model failed to initialize. Cannot load vector store.")
            st.stop()
            return None
            
        if not config.CHROMA_DB_PATH.exists() or not any(config.CHROMA_DB_PATH.iterdir()):
            st.warning(f"ChromaDB not found at {config.CHROMA_DB_PATH}. Please run the ingestion pipeline ('python ingest.py') first.")
            st.stop()
            return None

        vectorstore = Chroma(persist_directory=str(config.CHROMA_DB_PATH), embedding_function=embeddings)
        logger.info("ChromaDB loaded successfully.")
        return vectorstore
    except Exception as e:
        logger.error(f"Error loading ChromaDB: {e}. Ensure the ingestion pipeline has run successfully.", exc_info=True)
        st.error(f"Error loading ChromaDB: {e}. Please ensure the data ingestion pipeline has been run.")
        st.stop()
        return None