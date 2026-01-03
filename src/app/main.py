import streamlit as st
import logging
import re
from langchain_core.messages import HumanMessage, AIMessage
from src.app.chain import get_chain_manager

logger = logging.getLogger(__name__)

# --- Mode Selection Logic ---
def get_query_mode(query: str) -> str:
    """
    Analyzes the user query to determine the appropriate prompt mode.
    """
    query = query.lower()
    if any(keyword in query for keyword in ["résume", "résumer", "synthétise", "synthétiser"]):
        logger.info("Query identified as 'summary' mode.")
        return "summary"
    elif any(keyword in query for keyword in ["combien", "quel est le score", "statistique", "donnée"]):
        logger.info("Query identified as 'stats' mode.")
        return "stats"
    else:
        logger.info("Query identified as 'default' mode.")
        return "default"

# --- Streamlit UI Components ---
def display_message(role, content):
    """Displays a chat message in the Streamlit UI."""
    if role == "user":
        st.markdown(f'<div class="chat-message-user">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message-ai">{content}</div>', unsafe_allow_html=True)

def main_streamlit_app():
    """Main function for the Streamlit RAG application, using the new Prompt Management Architecture."""
    st.set_page_config(page_title="CAN Assistant Pro (Local LLM)", page_icon="⚽", layout="wide")

    # Apply custom CSS
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #800000, #B2382D);
        background-attachment: fixed;
    }
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stTextInput > div > div > input { border-radius: 10px; border: 1px solid #07A88F; padding: 10px; }
    .stButton > button { background-color: #07A88F; color: white; border-radius: 10px; border: none; padding: 10px 20px; font-weight: bold; }
    .chat-message-user { background-color: #FFFFFF; color: #000000; border: 1px solid #07A88F; padding: 10px; border-radius: 10px; margin-bottom: 10px; margin-left: 20%; text-align: right; box-shadow: 2px 2px 5px rgba(0,0,0,0.2); }
    .chat-message-ai { background: linear-gradient(to right, #07A88F, #FDB913); color: #FFFFFF; padding: 10px; border-radius: 10px; margin-bottom: 10px; margin-right: 20%; text-align: left; box-shadow: 2px 2px 5px rgba(0,0,0,0.2); }
    .stHeader { background-color: rgba(0,0,0,0.5); backdrop-filter: blur(10px); padding: 10px; border-radius: 10px; margin-bottom: 20px; }
    .stTitle { color: #FDB913 !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="stHeader"><h1 class="stTitle">CAN Assistant Pro ⚽ (Local LLM)</h1></div>', unsafe_allow_html=True)
    st.markdown("### Votre expert IA pour la Coupe d'Afrique des Nations 2025")

    # --- RAG Pipeline Initialization ---
    try:
        chain_manager = get_chain_manager()
    except Exception as e:
        st.error(f"Erreur critique lors de l'initialisation du gestionnaire de chaîne RAG: {e}")
        logger.error(f"Critical error during RAG chain manager initialization: {e}", exc_info=True)
        st.stop()

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat messages from history on app rerun
    for message in st.session_state.get("messages_display", []):
        display_message(message["role"], message["content"])

    # Chat input
    user_query = st.chat_input("Posez votre question ici...")

    if user_query:
        if "messages_display" not in st.session_state:
             st.session_state.messages_display = []
        st.session_state.messages_display.append({"role": "user", "content": user_query})
        display_message("user", user_query)

        # Get mode based on query
        mode = get_query_mode(user_query)
        st.session_state.chat_history.append(HumanMessage(content=user_query))

        with st.spinner(f"L'assistant réfléchit (Mode: {mode})..."):
            try:
                # Get the appropriate chain from the manager
                rag_chain = chain_manager.get_rag_chain(mode=mode)
                
                # Invoke the RAG chain
                response = rag_chain.invoke({
                    "chat_history": st.session_state.chat_history,
                    "input": user_query
                })
                # The response from a pure LCEL chain with StrOutputParser is just a string
                ai_response_content = response
                st.session_state.messages_display.append({"role": "assistant", "content": ai_response_content})
                st.session_state.chat_history.append(AIMessage(content=ai_response_content))
                display_message("assistant", ai_response_content)

            except Exception as e:
                error_message = f"Désolé, une erreur est survenue: {e}"
                st.session_state.messages_display.append({"role": "assistant", "content": error_message})
                st.session_state.chat_history.append(AIMessage(content=error_message))
                display_message("assistant", error_message)
                logger.error(f"Error while invoking RAG chain: {e}", exc_info=True)
    
    # Sidebar for additional features
    with st.sidebar:
        st.header("CAN Assistant Pro")
        st.markdown("---")
        if st.button("Effacer la conversation"):
            st.session_state.chat_history = []
            st.session_state.messages_display = []
            st.rerun()