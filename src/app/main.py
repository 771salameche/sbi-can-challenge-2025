import streamlit as st
import logging
from langchain_core.messages import HumanMessage, AIMessage
from src import config
from src.app.retrieval import setup_rag_chain

logger = logging.getLogger(__name__)

# --- Streamlit UI Components ---
def display_message(role, content):
    """Displays a chat message in the Streamlit UI."""
    if role == "user":
        st.markdown(f'<div class="chat-message-user">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message-ai">{content}</div>', unsafe_allow_html=True)

def main_streamlit_app():
    """Main function for the Streamlit RAG application."""
    st.set_page_config(page_title="CAN Assistant Pro RAG Chatbot", page_icon="⚽", layout="wide")

    # Apply custom CSS
    st.markdown(r'''
    <style>
    .stApp { background: linear-gradient(to bottom right, #800000, #B2382D); background-attachment: fixed; }
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stTextInput > div > div > input { border-radius: 10px; border: 1px solid #07A88F; padding: 10px; }
    .stButton > button { background-color: #07A88F; color: white; border-radius: 10px; border: none; padding: 10px 20px; font-weight: bold; }
    .chat-message-user { background-color: #FFFFFF; color: #000000; border: 1px solid #07A88F; padding: 10px; border-radius: 10px; margin-bottom: 10px; margin-left: 20%; text-align: right; box-shadow: 2px 2px 5px rgba(0,0,0,0.2); }
    .chat-message-ai { background: linear-gradient(to right, #07A88F, #FDB913); color: #FFFFFF; padding: 10px; border-radius: 10px; margin-bottom: 10px; margin-right: 20%; text-align: left; box-shadow: 2px 2px 5px rgba(0,0,0,0.2); }
    .stHeader { background-color: rgba(0,0,0,0.5); backdrop-filter: blur(10px); padding: 10px; border-radius: 10px; margin-bottom: 20px; }
    .stTitle { color: #FDB913 !important; text-align: center; }
    </style>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="stHeader"><h1 class="stTitle">CAN Assistant Pro ⚽</h1></div>', unsafe_allow_html=True)
    st.markdown("### Votre expert IA pour la Coupe d\'Afrique des Nations 2025")

    # --- RAG Pipeline Initialization ---
    rag_chain = None
    with st.spinner("Chargement de l\'assistant IA..."):
        try:
            rag_chain = setup_rag_chain()
        except Exception as e:
            st.error(f"Erreur lors de l\'initialisation du pipeline RAG: {e}")
            logger.error(f"Error during RAG pipeline initialization: {e}", exc_info=True)
            st.stop()

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "messages_display" not in st.session_state:
        st.session_state.messages_display = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages_display:
        display_message(message["role"], message["content"])

    # Chat input
    user_query = st.chat_input("Posez votre question ici...")

    if user_query:
        st.session_state.messages_display.append({"role": "user", "content": user_query})
        display_message("user", user_query)
        st.session_state.chat_history.append(HumanMessage(content=user_query))

        with st.spinner("L\'assistant réfléchit..."):
            try:
                # Invoke the RAG chain
                response = rag_chain.invoke({
                    "chat_history": st.session_state.chat_history,
                    "input": user_query
                })
                ai_response_content = response["answer"]
                st.session_state.messages_display.append({"role": "assistant", "content": ai_response_content})
                st.session_state.chat_history.append(AIMessage(content=ai_response_content))
                display_message("assistant", ai_response_content)

            except Exception as e:
                error_message = f"Désolé, une erreur est survenue lors de la récupération de la réponse: {e}"
                st.session_state.messages_display.append({"role": "assistant", "content": error_message})
                st.session_state.chat_history.append(AIMessage(content=error_message))
                display_message("assistant", error_message)
                logger.error(f"Error while invoking RAG chain: {e}", exc_info=True)
    
    # Sidebar for additional features
    with st.sidebar:
        st.header("CAN Assistant Pro")
        st.markdown("---")
        st.subheader("Actions")
        if st.button("Effacer la conversation"):
            st.session_state.chat_history = []
            st.session_state.messages_display = []
            st.rerun()
        
        st.markdown("---")
        st.subheader("Exemples de questions")
        example_questions = [
            "Quand commence la CAN 2025 ?",
            "Quels sont les stades au Maroc pour la CAN 2025 ?",
            "Qui a gagné la dernière CAN ?",
            "Quelles sont les équipes du Groupe A de la CAN 2025 ?",
            "Qui est le meilleur buteur de l'histoire de la CAN ?",
            "Quels sont les règlements officiels de la CAN 2025 concernant les listes d'équipes ?"
        ]
        for i, q in enumerate(example_questions):
            if st.button(q, key=f"example_q_{i}"):
                # This causes a rerun, and the chat_input will be populated.
                # However, direct population of st.chat_input is not supported.
                # A common workaround is to update a session state var and then use that.
                st.session_state["submitted_query"] = q
                st.rerun()

    # Handle submitted_query from example buttons
    if "submitted_query" in st.session_state and st.session_state["submitted_query"]:
        user_query = st.session_state["submitted_query"]
        del st.session_state["submitted_query"] # Clear it after use
        # Manually trigger processing for the submitted query
        if user_query:
            st.session_state.messages_display.append({"role": "user", "content": user_query})
            display_message("user", user_query)
            st.session_state.chat_history.append(HumanMessage(content=user_query))

            with st.spinner("L\'assistant réfléchit..."):
                try:
                    response = rag_chain.invoke({
                        "chat_history": st.session_state.chat_history,
                        "input": user_query
                    })
                    ai_response_content = response["answer"]
                    st.session_state.messages_display.append({"role": "assistant", "content": ai_response_content})
                    st.session_state.chat_history.append(AIMessage(content=ai_response_content))
                    display_message("assistant", ai_response_content)
                except Exception as e:
                    error_message = f"Désolé, une erreur est survenue lors de la récupération de la réponse: {e}"
                    st.session_state.messages_display.append({"role": "assistant", "content": error_message})
                    st.session_state.chat_history.append(AIMessage(content=error_message))
                    display_message("assistant", error_message)
                    logger.error(f"Error while invoking RAG chain from example button: {e}", exc_info=True)
