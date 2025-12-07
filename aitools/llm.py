from openai import AsyncAzureOpenAI
import config
from pydantic import BaseModel
from typing import List

client = AsyncAzureOpenAI(azure_deployment=config.AZURE_DEPLOYMENT, api_version=config.AZURE_API_VERSION, azure_endpoint=config.AZURE_ENDPOINT, api_key=config.AZURE_OPENAI_API_KEY)

nano_client = AsyncAzureOpenAI(azure_deployment=config.AZURE_DEPLOYMENT_NANO, api_version=config.AZURE_API_VERSION_NANO, azure_endpoint=config.AZURE_ENDPOINT_NANO, api_key=config.AZURE_OPENAI_API_KEY_NANO)

class Query(BaseModel):
    question: str

class Queries(BaseModel):
    questions: List[Query]

async def get_llm_questions(user_query, top_k=3):
    """Send user query to get enhanced questions from LLM""" 
    prompt = f"""
На основе вопроса пользователя составь список запросов по RAG базе данных с законами, чтобы получить релевантные статьи по законам Кыргызстана.

Вопрос: {user_query}
"""

    try:
        response = await nano_client.responses.parse(
            model=config.AZURE_DEPLOYMENT_NANO,
            instructions="Ты юридический помощник, который помогает людям понимать законы.",
            input=prompt,
            text_format=Queries
        )
        return [q.question for q in response.output_parsed.questions[:top_k]]
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None


async def get_llm_response(user_query, top_results):
    """Send top results to LLM for analysis"""
    # Prepare context from top 3 results
    context = "\n\n".join([
        f"Источник: {result['path']}\n"
        f"Текст: {result['text']}"
        for result in top_results
    ])
    
    prompt = f"""
На основе следующих релевантных статей закона, ответь на вопрос пользователя.

Вопрос: {user_query}

Релевантные статьи:
{context}

Пожалуйста, дай подробный ответ, ссылаясь на конкретные статьи."""

    try:
        response = await nano_client.responses.create(
            model=config.AZURE_DEPLOYMENT_NANO,
            instructions="Ты юридический помощник, который помогает людям понимать законы.",
            input=prompt
        )
        return response.output_text
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None
