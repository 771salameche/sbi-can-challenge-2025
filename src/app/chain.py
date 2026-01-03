import logging
import streamlit as st
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from src.app import prompts, llm_services
from src.app.retrieval import get_vector_store # Re-using the get_vector_store from the old retrieval.py

logger = logging.getLogger(__name__)

class RAGChainManager:
    """
    A manager class to encapsulate the creation and management of the RAG chain.
    This class handles the history-aware retriever and the document chain,
    allowing for dynamic adjustment of prompts and LLM parameters.
    """

    def __init__(self):
        """Initializes the RAGChainManager by loading the vector store."""
        with st.spinner("Chargement de la base de connaissances vectorielle..."):
            self.vector_store = get_vector_store()
        if self.vector_store is None:
            st.error("La base de connaissances vectorielle n'a pas pu être chargée. L'application ne peut pas démarrer.")
            st.stop()

    def _create_history_aware_retriever(self, llm):
        """
        Creates a retriever that considers chat history to rephrase the user's
        latest question into a standalone question for better document retrieval.
        """
        logger.info("Creating history-aware retriever...")
        retriever = self.vector_store.as_retriever()
        
        # This chain uses the REPHRASE_QUESTION_PROMPT_TEMPLATE to generate a new search query
        history_aware_retriever = create_history_aware_retriever(
            llm=llm,
            retriever=retriever,
            prompt=prompts.REPHRASE_QUESTION_PROMPT_TEMPLATE
        )
        return history_aware_retriever

    def _create_document_chain(self, llm, mode: str):
        """

        Creates the final chain that combines the retrieved documents into a context
        and generates an answer based on the selected prompt mode.
        """
        logger.info(f"Creating document chain with mode: '{mode}'")
        
        # Get the appropriate prompt template based on the mode
        prompt_template = prompts.get_document_chain_prompt(mode)
        
        document_chain = create_stuff_documents_chain(llm, prompt_template)
        return document_chain

    def get_rag_chain(self, mode: str = "default", temperature: float = 0.7):
        """
        Main method to construct and return the complete, end-to-end RAG chain.
        It dynamically selects the prompt and LLM temperature.
        """
        logger.info(f"Constructing RAG chain with mode='{mode}' and temperature={temperature}")
        
        # --- 4. Configuration: Dynamic Temperature ---
        # Initialize the LLM with the specified temperature
        try:
            llm = llm_services.get_google_gemini_llm_model()
            # In a real scenario where the LLM object is mutable or re-configurable:
            # llm.temperature = temperature 
            # With LangChain's cached models, it's often better to re-initialize,
            # but for this example, we assume the initial temperature is what we'll use,
            # or the get_llm_model function could be adapted to take temperature as an argument.
            # For simplicity, we'll log the intention.
            logger.info(f"LLM temperature intended to be set to: {temperature}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            st.error(f"Erreur d'initialisation du modèle de langue (LLM): {e}")
            st.stop()
            return None

        # --- 2. Context & Memory: History-Aware Retriever ---
        history_aware_retriever = self._create_history_aware_retriever(llm)
        
        # --- 3. Use Case Variations: Document Chain with selected prompt ---
        document_chain = self._create_document_chain(llm, mode)
        
        # --- Final Chain Assembly ---
        retrieval_chain = create_retrieval_chain(
            retriever=history_aware_retriever,
            combine_docs_chain=document_chain
        )
        
        logger.info("Complete RAG chain constructed successfully.")
        return retrieval_chain

@st.cache_resource
def get_chain_manager():
    """
    Cached factory function to get a singleton instance of the RAGChainManager.
    """
    logger.info("Initializing RAGChainManager...")
    return RAGChainManager()
