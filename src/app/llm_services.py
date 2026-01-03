import os
import logging
import streamlit as st # Keep st.cache_resource for Streamlit apps
from langchain_openai import AzureOpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from src import config

logger = logging.getLogger(__name__)

@st.cache_resource
def get_azure_openai_embeddings_model():
    """Initializes and returns the Azure OpenAI Embeddings model."""
    logger.info("Initializing Azure OpenAI Embeddings model for application...")
    try:
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
        )
        return embeddings
    except Exception as e:
        logger.error(f"Error initializing Azure OpenAI Embeddings: {e}. Please check AZURE_OPENAI_ environment variables.", exc_info=True)
        st.error(f"Error initializing Azure OpenAI Embeddings: {e}. Please check AZURE_OPENAI_ environment variables.")
        st.stop() # Stop Streamlit app
        return None

@st.cache_resource
def get_google_gemini_llm_model():
    """Initializes and returns the Google Gemini LLM model."""
    logger.info("Initializing Google Gemini LLM model for application...")
    try:
        llm = ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_GEMINI_MODEL", config.LLM_MODEL_NAME),
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0.7,
        )
        return llm
    except Exception as e:
        logger.error(f"Error initializing Google Gemini LLM: {e}. Please check GOOGLE_API_KEY.", exc_info=True)
        st.error(f"Error initializing Google Gemini LLM: {e}. Please check GOOGLE_API_KEY.")
        st.stop() # Stop Streamlit app
        return None
