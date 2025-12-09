"""
Configuration module for Azure OpenAI API credentials.

This module loads environment variables from a .env file and exposes
them as module-level constants for use throughout the application.
Optimized for performance with caching and lazy loading.
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Final, List, Optional

from dotenv import load_dotenv


def _load_env() -> None:
    """
    Load environment variables from .env file.
    
    Searches for .env in project root directory.
    Falls back to current directory if not found.
    """
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()


# Load environment variables once at module import
_load_env()

# Type aliases for configuration
ConfigValue = Optional[str]

# Azure OpenAI Nano deployment configuration (primary)
AZURE_ENDPOINT_NANO: Final[ConfigValue] = os.environ.get("AZURE_ENDPOINT_NANO")
AZURE_OPENAI_API_KEY_NANO: Final[ConfigValue] = os.environ.get(
    "AZURE_OPENAI_API_KEY_NANO"
)
AZURE_DEPLOYMENT_NANO: Final[ConfigValue] = os.environ.get("AZURE_DEPLOYMENT_NANO")
AZURE_API_VERSION_NANO: Final[ConfigValue] = os.environ.get(
    "AZURE_API_VERSION_NANO"
)

# Telegram Bot configuration
TELEGRAM_BOT_TOKEN: Final[ConfigValue] = os.environ.get("TELEGRAM_BOT_TOKEN")

# Supported languages
SUPPORTED_LANGUAGES: Final[tuple] = ('ru', 'kg')

# Prompt templates - stored as constants to avoid recreation
_QUESTIONS_PROMPTS: Final[Dict[str, str]] = {
    'ru': (
        "На основе вопроса пользователя составь список запросов "
        "по RAG базе данных с законами для получения релевантных "
        "статей по законам Кыргызстана.\n\nВопрос: {user_query}"
    ),
    'kg': (
        "Колдонуучунун суроосунун негизинде Кыргызстан мыйзамдары "
        "боюнча RAG маалымат базасынан тиешелүү беренелерди алуу "
        "үчүн суроо-талаптардын тизмесин түз.\n\nСуроо: {user_query}"
    )
}

_RESPONSE_PROMPTS: Final[Dict[str, str]] = {
    'ru': (
        "На основе следующих релевантных статей закона, ответь на "
        "вопрос пользователя.\n\nВопрос: {user_query}\n\n"
        "Релевантные статьи:\n{context}\n\n"
        "Дай подробный ответ, ссылаясь на конкретные статьи."
    ),
    'kg': (
        "Төмөндө берілген мыйзамдын тиешелүү беренелеринин негизинде "
        "колдонуучунун суроосуна жооп бер.\n\nСуроо: {user_query}\n\n"
        "Тиешелүү беренелер:\n{context}\n\n"
        "Так беренелерге шилтеме берүү менен кеңири жооп бер."
    )
}


@lru_cache(maxsize=128)
def get_questions_prompt(user_query: str, lang: str = 'ru') -> str:
    """
    Generate a prompt for creating search queries based on user question.
    
    Uses LRU cache to avoid regenerating identical prompts.
    
    Parameters:
        user_query (str): The user's original question.
        lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.
    
    Returns:
        str: Formatted prompt string for the LLM.
    """
    template = _QUESTIONS_PROMPTS.get(lang, _QUESTIONS_PROMPTS['ru'])
    return template.format(user_query=user_query)


def get_response_prompt(user_query: str, context: str, lang: str = 'ru') -> str:
    """
    Generate a prompt for generating response based on context.
    
    Not cached due to variable context parameter.
    
    Parameters:
        user_query (str): The user's original question.
        context (str): Relevant law articles as context.
        lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.
    
    Returns:
        str: Formatted prompt string for the LLM.
    """
    template = _RESPONSE_PROMPTS.get(lang, _RESPONSE_PROMPTS['ru'])
    return template.format(user_query=user_query, context=context)


def concat_query_and_doc(query: str, doc_data: List[str]) -> str:
    """
    Concatenate user query with document data for processing.
    
    Parameters:
        query (str): User's question about the document.
        doc_data (List[str]): List of extracted document paragraphs.
    
    Returns:
        str: Combined query and document text.
    """
    doc_text = "\n".join(doc_data)
    return f"Question: {query}\n\nDocument:\n{doc_text}"
