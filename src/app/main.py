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
def display_message(role, content, mascott_b64, coupe_b64):
    """Displays a chat message in the Streamlit UI."""
    if role == "user":
        st.markdown(f'<div class="chat-message-user">{content}</div>', unsafe_allow_html=True)
    else:
        # For AI messages, include the avatar and the expert badge
        badge_html = f'<span class="expert-badge"><img src="data:image/svg+xml;base64,{coupe_b64}" class="mini-coupe"> Expert CAN</span>'
        message_html = f'''
        <div class="chat-message-ai">
            <img src="data:image/png;base64,{mascott_b64}" class="ai-avatar">
            <div class="ai-content">
                {badge_html}
                <p>{content}</p>
            </div>
        </div>
        '''
        st.markdown(message_html, unsafe_allow_html=True)
        st.session_state.ai_responding = False

import streamlit as st
import logging
import re
from langchain_core.messages import HumanMessage, AIMessage
from src.app.chain import get_chain_manager
import base64
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Asset Handling ---
def get_image_as_base64(path_str: str) -> str:
    """Read an image file and return it as a base64 encoded string."""
    path = Path(path_str)
    if not path.is_file():
        logger.error(f"Image file not found at {path}")
        return ""
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception as e:
        logger.error(f"Error reading or encoding image {path}: {e}")
        return ""

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
def display_message(role, content, mascott_b64, coupe_b64):
    """Displays a chat message in the Streamlit UI."""
    if role == "user":
        st.markdown(f'<div class="chat-message-user">{content}</div>', unsafe_allow_html=True)
    else:
        # For AI messages, include the avatar and the expert badge
        badge_html = f'<span class="expert-badge"><img src="data:image/svg+xml;base64,{coupe_b64}" class="mini-coupe"> Expert CAN</span>'
        message_html = f'''
        <div class="chat-message-ai">
            <img src="data:image/png;base64,{mascott_b64}" class="ai-avatar">
            <div class="ai-content">
                {badge_html}
                <p>{content}</p>
            </div>
        </div>
        '''
        st.markdown(message_html, unsafe_allow_html=True)
        st.session_state.ai_responding = False

def main_streamlit_app():
    """Main function for the Streamlit RAG application, with integrated visual assets."""
    st.set_page_config(page_title="CAN Assistant Pro", page_icon="⚽", layout="wide")

    # --- Load and Encode Assets ---
    assets_path = Path(__file__).parent / "public"
    coupe_b64 = get_image_as_base64(str(assets_path / "coupe.svg"))
    logo_b64 = get_image_as_base64(str(assets_path / "logo.png"))
    ball_b64 = get_image_as_base64(str(assets_path / "png-ball.png"))
    mascott_b64 = get_image_as_base64(str(assets_path / "mascott.png"))
    
    flags = {
        "Algérie": get_image_as_base64(str(assets_path / "logo_alg.svg")),
        "Cameroun": get_image_as_base64(str(assets_path / "logo_cmr.svg")),
        "Égypte": get_image_as_base64(str(assets_path / "logo_egy.svg")),
        "Maroc": get_image_as_base64(str(assets_path / "logo_mar.svg")),
        "Nigeria": get_image_as_base64(str(assets_path / "logo_ngr.svg")),
        "Sénégal": get_image_as_base64(str(assets_path / "logo_sen.svg")),
    }
    
    # Initialize session state for mascot visibility
    if "ai_responding" not in st.session_state:
        st.session_state.ai_responding = False

    # Apply custom CSS
    st.markdown(f"""
    <style>
        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-20px); }}
            100% {{ transform: translateY(0px); }}
        }}

        .stApp {{
            background-color: #800000;
            background-attachment: fixed;
        }}
        
        .floating-ball {{
            position: fixed;
            bottom: -50px;
            right: 10%;
            width: 150px;
            height: auto;
            z-index: 0;
            animation: float 6s ease-in-out infinite;
        }}

        .mascott-container {{
            position: fixed;
            bottom: 0;
            left: 10px;
            width: 250px;
            height: auto;
            z-index: 10;
            transition: opacity 0.5s ease-in-out, transform 0.5s ease-in-out;
            opacity: {'1' if st.session_state.get('ai_responding', False) else '0'};
            transform: {'translateY(0)' if st.session_state.get('ai_responding', False) else 'translateY(100%)'};
        }}
        
        .main-header {{
            position: relative;
            background-color: rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            padding: 5px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}

        .main-logo {{
            width: 300px;
            height: auto;
        }}

        .top-right-logo {{
            position: absolute;
            top: 10px;
            right: 15px;
            width: 70px;
            height: auto;
        }}
        
        .main .block-container {{ padding-top: 1rem; padding-bottom: 2rem; }}
        .stTextInput > div > div > input {{ border-radius: 10px; border: 1px solid #07A88F; padding: 10px; color: #000000; }}
        .stButton > button {{ background-color: #07A88F; color: #FFFFFF; border-radius: 10px; border: none; padding: 10px 20px; font-weight: bold; }}
        
        .chat-message-user {{ background-color: #FFFFFF; color: #000000; border: 1px solid #B2382D; padding: 10px; border-radius: 10px; margin-bottom: 10px; margin-left: 20%; text-align: right; box-shadow: 2px 2px 5px rgba(0,0,0,0.2); }}
        
        .chat-message-ai {{
            display: flex;
            align-items: flex-start;
            background: #FFFFFF;
            color: #006051;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            margin-right: 20%;
            text-align: left;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        }}
        
        .ai-avatar {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            margin-right: 15px;
            border: 2px solid #07A88F;
        }}
        .ai-content p {{
            margin: 0;
            padding-top: 5px;
        }}

        .expert-badge {{
            background-color: #07A88F;
            color: #FFFFFF;
            padding: 3px 8px;
            border-radius: 5px;
            font-size: 0.8em;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
        }}
        .mini-coupe {{
            width: 16px;
            height: 16px;
            margin-right: 5px;
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background-color: #006051;
            color: #FFFFFF;
        }}
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
             color: #FDB913;
        }}
        .flag-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
        }}
        .flag-item {{
            text-align: center;
        }}
        .flag-item a {{
            display: block;
            transition: transform 0.2s;
        }}
        .flag-item a:hover {{
            transform: scale(1.1);
        }}
        .flag-image {{
            width: 50px;
            height: 50px;
            object-fit: contain;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # --- Floating Ball and Mascot ---
    st.markdown(f'<img src="data:image/png;base64,{ball_b64}" class="floating-ball">', unsafe_allow_html=True)
    st.markdown(f'<div class="mascott-container"><img src="data:image/png;base64,{mascott_b64}" style="width:100%;"></div>', unsafe_allow_html=True)

    # --- Header ---
    st.markdown(f'''
    <div class="main-header">
        <img src="data:image/svg+xml;base64,{coupe_b64}" class="main-logo">
        <img src="data:image/png;base64,{logo_b64}" class="top-right-logo">
    </div>
    ''', unsafe_allow_html=True)
    st.markdown("### Votre expert IA pour la Coupe d'Afrique des Nations 2025", unsafe_allow_html=True)

    # --- RAG Pipeline Initialization ---
    try:
        chain_manager = get_chain_manager()
    except Exception as e:
        st.error(f"Erreur critique lors de l'initialisation du gestionnaire de chaîne RAG: {{e}}")
        logger.error(f"Critical error during RAG chain manager initialization: {{e}}", exc_info=True)
        st.stop()

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat messages from history on app rerun
    for message in st.session_state.get("messages_display", []):
        display_message(message["role"], message["content"], mascott_b64, coupe_b64)

    # Chat input
    user_query = st.chat_input("Posez votre question ici...")

    if user_query:
        if "messages_display" not in st.session_state:
             st.session_state.messages_display = []
        st.session_state.messages_display.append({{"role": "user", "content": user_query}})
        display_message("user", user_query, mascott_b64, coupe_b64)

        mode = get_query_mode(user_query)
        st.session_state.chat_history.append(HumanMessage(content=user_query))
        
        # Set state to show mascot, then rerun to update UI
        st.session_state.ai_responding = True
        st.rerun()

    if st.session_state.ai_responding:
        last_query = st.session_state.chat_history[-1].content
        mode = get_query_mode(last_query)

        with st.spinner(f"L'assistant réfléchit (Mode: {{mode}})..."):
            try:
                rag_chain = chain_manager.get_rag_chain(mode=mode)
                response = rag_chain.invoke({
                    "chat_history": st.session_state.chat_history,
                    "input": last_query
                })
                ai_response_content = response
                st.session_state.messages_display.append({{"role": "assistant", "content": ai_response_content}})
                st.session_state.chat_history.append(AIMessage(content=ai_response_content))
                
                # Immediately hide mascot and rerun to display message
                st.session_state.ai_responding = False
                st.rerun()

            except Exception as e:
                error_message = f"Désolé, une erreur est survenue: {{e}}"
                st.session_state.messages_display.append({{"role": "assistant", "content": error_message}})
                st.session_state.chat_history.append(AIMessage(content=error_message))
                logger.error(f"Error while invoking RAG chain: {{e}}", exc_info=True)
                
                # Hide mascot on error and rerun
                st.session_state.ai_responding = False
                st.rerun()

    # Sidebar for additional features
    with st.sidebar:
        st.header("CAN Assistant Pro")
        st.markdown("---")
        
        st.subheader("Équipes favorites")
        flag_html = '<div class="flag-container">'
        for country, b64_str in flags.items():
            if b64_str:
                flag_html += f'''
                <div class="flag-item">
                    <a href="#" title="{country}">
                        <img src="data:image/svg+xml;base64,{b64_str}" class="flag-image">
                    </a>
                </div>
                '''
        flag_html += '</div>'
        st.markdown(flag_html, unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("Effacer la conversation"):
            st.session_state.chat_history = []
            st.session_state.messages_display = []
            st.session_state.ai_responding = False
            st.rerun()