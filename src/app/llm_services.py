import logging
import streamlit as st
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_openai import AzureOpenAIEmbeddings
from src import config

logger = logging.getLogger(__name__)

# This function for Azure embeddings remains unchanged.
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
        st.stop()
        return None

# Renamed the function to be more accurate
@st.cache_resource
def get_huggingface_chat_llm():
    """
    Initializes a LangChain Chat LLM object that calls a conversational model 
    on the Hugging Face Inference API.
    """
    logger.info("Initializing Hugging Face Chat endpoint (Mistral-7B-Instruct-v0.2)...")
    
    repo_id = "mistralai/Mistral-7B-Instruct-v0.2"
    
    try:
        # 1. Create the object that connects to the remote API endpoint
        llm_endpoint = HuggingFaceEndpoint(
            repo_id=repo_id,
            huggingfacehub_api_token=config.HUGGINGFACEHUB_API_TOKEN,
            temperature=0.2,
            max_new_tokens=512,
        )
        
        # 2. Wrap the endpoint in the ChatHuggingFace class to make it
        #    conform to the standard chat model interface for LCEL.
        chat_model = ChatHuggingFace(llm=llm_endpoint)
        
        logger.info("Hugging Face Chat endpoint loaded successfully.")
        return chat_model
        
    except Exception as e:
        error_message = f"Failed to initialize Hugging Face Chat API for model '{repo_id}'. Ensure your HUGGINGFACEHUB_API_TOKEN is correct. Error: {e}"
        logger.error(error_message, exc_info=True)
        st.error(error_message)
        st.stop()
        return None
