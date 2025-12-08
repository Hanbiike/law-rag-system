"""
Configuration module for Azure OpenAI API credentials.

This module loads environment variables from a .env file and exposes
them as module-level constants for use throughout the application.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Find .env file in project root
env_path = Path(__file__).parent.parent / '.env'

# Load environment variables from .env file
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✓ Loaded .env from: {env_path}")
else:
    print(f"⚠ Warning: .env file not found at {env_path}")
    load_dotenv()  # Try to load from current directory

# Azure OpenAI primary deployment configuration
AZURE_ENDPOINT: Optional[str] = os.environ.get("AZURE_ENDPOINT")
AZURE_OPENAI_API_KEY: Optional[str] = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT: Optional[str] = os.environ.get("AZURE_DEPLOYMENT")
AZURE_API_VERSION: Optional[str] = os.environ.get("AZURE_API_VERSION")

# Azure OpenAI Nano deployment configuration
AZURE_ENDPOINT_NANO: Optional[str] = os.environ.get("AZURE_ENDPOINT_NANO")
AZURE_OPENAI_API_KEY_NANO: Optional[str] = os.environ.get(
    "AZURE_OPENAI_API_KEY_NANO"
)
AZURE_DEPLOYMENT_NANO: Optional[str] = os.environ.get("AZURE_DEPLOYMENT_NANO")
AZURE_API_VERSION_NANO: Optional[str] = os.environ.get(
    "AZURE_API_VERSION_NANO"
)

def get_questions_prompt(user_query, lang = 'ru'):
    if lang == 'ru':
        prompt = f"""
        На основе вопроса пользователя составь список запросов по RAG базе данных с законами, чтобы получить релевантные статьи по законам Кыргызстана.

        Вопрос: {user_query}
        """
    elif lang == 'kg':
        prompt = f"""
        Колдонуучунун суроосунун негизинде Кыргызстан мыйзамдары боюнча RAG маалымат базасынан тиешелүү беренелерди алуу үчүн суроо-талаптардын тизмесин түз.

        Суроо: {user_query}
        """

    return prompt

def get_response_prompt(user_query, context, lang = 'ru'):
    if lang == 'ru':
        prompt = f"""
        На основе следующих релевантных статей закона, ответь на вопрос пользователя.

        Вопрос: {user_query}

        Релевантные статьи:
        {context}

        Пожалуйста, дай подробный ответ, ссылаясь на конкретные статьи."""
    elif lang == 'kg':
        prompt = f"""
        Төмөндө берілген мыйзамдын тиешелүү беренелеринин негизинде колдонуучунун суроосуна жооп бер.

        Суроо: {user_query}

        Тиешелүү беренелер:
        {context}

        Сураныч, так беренелерге шилтеме берүү менен кеңири жооп бер.
        """

    return prompt

def concat_query_and_doc(query: str, doc_data: list) -> str:
    doc_text = "\n".join(doc_data)
    return f"Question: {query}\n\nDocument:\n{doc_text}"
