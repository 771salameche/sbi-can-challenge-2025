import logging
import streamlit as st
from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from src.app import prompts, llm_services
from src.app.retrieval import get_vector_store

logger = logging.getLogger(__name__)

class RAGChainManager:
    """
    A manager class to encapsulate the creation and management of the RAG chain
    using the LangChain Expression Language (LCEL).
    """

    def __init__(self):
        """Initializes the RAGChainManager by loading the vector store."""
        with st.spinner("Chargement de la base de connaissances vectorielle..."):
            self.vector_store = get_vector_store()
        if self.vector_store is None:
            st.error("La base de connaissances vectorielle n'a pas pu être chargée. L'application ne peut pas démarrer.")
            st.stop()

    def get_rag_chain(self, mode: str = "default"):
        """
        Main method to construct and return the complete, end-to-end RAG chain using LCEL.
        It dynamically selects the prompt.
        """
        logger.info(f"Constructing LCEL RAG chain with mode='{mode}'")

        try:
            llm = llm_services.get_huggingface_chat_llm()
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            st.error(f"Erreur d'initialisation du modèle de langue (LLM): {e}")
            st.stop()
            return None

        # --- 1. History-Aware Standalone Question Chain ---
        # This chain takes the user's input and chat history, and formulates a
        # standalone question for the retriever.
        contextualize_q_chain = (
            prompts.REPHRASE_QUESTION_PROMPT_TEMPLATE
            | llm
            | StrOutputParser()
        )

        def get_standalone_question(input_dict):
            # If there's chat history, run the contextualization chain.
            # Otherwise, just use the user's direct input.
            if input_dict.get("chat_history"):
                return contextualize_q_chain
            else:
                return itemgetter("input")

        # --- 2. Document Retrieval and Formatting ---
        retriever = self.vector_store.as_retriever()
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # --- 3. Final Answer Generation Chain Assembly (LCEL) ---
        # Get the appropriate prompt template for the final answer.
        qa_prompt = prompts.get_document_chain_prompt(mode)
        
        # This is the main LCEL chain.
        rag_chain = (
            RunnablePassthrough.assign(
                # The 'context' is generated here. First, a standalone question is created.
                # That question is then passed to the retriever. The retrieved docs are
                # then formatted into a string.
                context=RunnableLambda(get_standalone_question) | retriever | format_docs
            )
            # The dictionary now contains 'input', 'chat_history', and 'context'.
            # This is piped into our final prompt.
            | qa_prompt
            # The formatted prompt is piped into the LLM.
            | llm
            # The LLM's output is parsed into a string.
            | StrOutputParser()
        )
        
        logger.info("Complete LCEL RAG chain constructed successfully.")
        return rag_chain

@st.cache_resource
def get_chain_manager():
    """
    Cached factory function to get a singleton instance of the RAGChainManager.
    """
    logger.info("Initializing RAGChainManager (LCEL)...")
    return RAGChainManager()