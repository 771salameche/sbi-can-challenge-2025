import logging
import streamlit as st # For st.cache_resource
from pathlib import Path
from langchain_chroma import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from src import config
from src.app.llm_services import get_google_gemini_llm_model, get_azure_openai_embeddings_model

logger = logging.getLogger(__name__)

@st.cache_resource
def get_vector_store():
    """Initializes and returns the ChromaDB vector store."""
    logger.info(f"Attempting to load ChromaDB from {config.CHROMA_DB_PATH}...")
    try:
        embeddings = get_azure_openai_embeddings_model() # Get embeddings for loading DB
        if embeddings is None:
            st.error("Embeddings model failed to initialize. Cannot load vector store.")
            st.stop()
            return None
            
        if not config.CHROMA_DB_PATH.exists() or not any(config.CHROMA_DB_PATH.iterdir()):
            st.warning(f"ChromaDB not found at {config.CHROMA_DB_PATH}. Please run the ingestion pipeline first.")
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

@st.cache_resource
def setup_rag_chain():
    """Sets up and returns the LangChain RAG chain."""
    logger.info("Setting up RAG chain...")
    try:
        llm = get_google_gemini_llm_model()
        if llm is None:
            st.error("LLM model failed to initialize. Cannot setup RAG chain.")
            st.stop()
            return None

        vectorstore = get_vector_store()
        if vectorstore is None:
            # Error message already shown in get_vector_store
            st.stop()
            return None

        retriever = vectorstore.as_retriever()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant specialized in the Africa Cup of Nations (CAN) 2025 in Morocco. "
                       "Answer the user's questions truthfully and concisely based on the provided context only. "
                       "If you don't know the answer or the context does not contain the information, just say 'Je ne dispose pas d\'informations suffisantes pour répondre à cette question.' "
                       "Do not try to make up an answer. Keep your answers in French.\n\n"
                       "Context: {context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
        ])

        document_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        logger.info("RAG chain setup complete.")
        return retrieval_chain
    except Exception as e:
        logger.error(f"Error setting up RAG chain: {e}", exc_info=True)
        st.error(f"Error setting up RAG chain: {e}. Please check logs for details.")
        st.stop()
        return None
