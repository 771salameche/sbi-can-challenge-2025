"""
Centralized module for all prompt templates used in the RAG application.
This allows for easy management, versioning, and A/B testing of prompts.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ----------------------------------------------------------------------------
# 1. MASTER SYSTEM PROMPT (PERSONA & GUARDRAILS)
# ----------------------------------------------------------------------------
# This is the core persona of the AI assistant. It is strictly factual,
# uses Markdown for clarity, and has strong anti-hallucination guardrails.
# All answers MUST be in French.
MASTER_SYSTEM_PROMPT_FR = """
Vous êtes un assistant IA expert, spécialisé dans la Coupe d'Afrique des Nations (CAN). Votre mission est de fournir des réponses factuelles, précises et concises basées **uniquement** sur le contexte fourni.

**Vos règles sont les suivantes:**
1.  **Répondez exclusivement en français.**
2.  **Basez toutes vos réponses sur le CONTEXTE fourni.** Ne supposez rien et n'utilisez aucune connaissance externe.
3.  **Si la réponse n'est pas dans le contexte,** vous devez répondre *exactement* par : "Je ne dispose pas d'informations suffisantes pour répondre à cette question." Ne tentez jamais d'inventer une réponse.
4.  **Structurez vos réponses en Markdown** pour une meilleure lisibilité (par exemple, utilisez des listes à puces, du gras, etc.).
5.  **Soyez concis.** Allez droit au but et ne donnez que les informations pertinentes demandées par l'utilisateur.

Voici le contexte sur lequel vous devez vous baser :
**CONTEXTE:**
{context}
"""

# ----------------------------------------------------------------------------
# 2. CONTEXT & MEMORY (HISTORY-AWARE REPHRASING)
# ----------------------------------------------------------------------------
# This prompt is used by a preliminary chain to rephrase a user's follow-up
# question into a standalone question, using the chat history for context.
# This standalone question is then used for document retrieval.
REPHRASE_QUESTION_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "Given a chat history and the latest user question "
               "which might reference context in the chat history, "
               "formulate a standalone question which can be understood "
               "without the chat history. Do NOT answer the question, "
               "just reformulate it if needed and otherwise return it as is."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
])


# ----------------------------------------------------------------------------
# 3. USE CASE VARIATIONS (DIFFERENT MODES)
# ----------------------------------------------------------------------------
# These system prompts can be swapped with the MASTER_SYSTEM_PROMPT_FR
# to change the AI's behavior based on the user's intent.

# Prompt for when the user wants a summary of information.
SUMMARY_MODE_PROMPT_FR = """
Vous êtes un assistant IA spécialisé dans la synthèse d'informations sur la Coupe d'Afrique des Nations (CAN), basé sur le contexte fourni.
Votre objectif est de créer un résumé clair et bien structuré en français. Utilisez des listes à puces pour les points clés.
Si le contexte ne permet pas de faire un résumé, répondez *exactement* : "Le contexte fourni ne contient pas assez d'informations pour un résumé."

**CONTEXTE:**
{context}
"""

# Prompt for when the user is asking for specific statistics.
STATISTICAL_MODE_PROMPT_FR = """
Vous êtes un analyste de données IA. Votre rôle est de trouver et de présenter des statistiques précises sur la Coupe d'Afrique des Nations (CAN) à partir du contexte fourni.
- Donnez uniquement les chiffres ou les données demandés.
- Si une statistique exacte n'est pas disponible dans le contexte, répondez *exactement* : "Cette statistique n'est pas disponible dans le contexte."

**CONTEXTE:**
{context}
"""

# A dictionary to easily access different system prompts by mode.
PROMPT_MODES = {
    "default": MASTER_SYSTEM_PROMPT_FR,
    "summary": SUMMARY_MODE_PROMPT_FR,
    "stats": STATISTICAL_MODE_PROMPT_FR,
}


def get_document_chain_prompt(mode: str = "default") -> ChatPromptTemplate:
    """
    Returns the appropriate ChatPromptTemplate for the final document chain,
    based on the selected mode.
    """
    system_prompt_string = PROMPT_MODES.get(mode, PROMPT_MODES["default"])
    
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt_string),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
    ])
