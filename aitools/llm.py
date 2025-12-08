from openai import AsyncAzureOpenAI
import confs.config as config
from pydantic import BaseModel
from typing import List, Optional, Any

class Query(BaseModel):
    """
    Модель для представления одного вопроса.
    """
    question: str

class Queries(BaseModel):
    """
    Модель для представления списка вопросов.
    """
    questions: List[Query]

class LLMHelper:
    """
    Класс-обёртка для работы с LLM через Azure OpenAI.
    Предоставляет методы для генерации уточняющих вопросов и получения ответа на основе релевантных статей.
    """

    def __init__(self) -> None:
        """
        Инициализация клиентов для разных деплоев Azure OpenAI.
        """
        # self.client = AsyncAzureOpenAI(
        #     azure_deployment=config.AZURE_DEPLOYMENT,
        #     api_version=config.AZURE_API_VERSION,
        #     azure_endpoint=config.AZURE_ENDPOINT,
        #     api_key=config.AZURE_OPENAI_API_KEY
        # )
        self.nano_client = AsyncAzureOpenAI(
            azure_deployment=config.AZURE_DEPLOYMENT_NANO,
            api_version=config.AZURE_API_VERSION_NANO,
            azure_endpoint=config.AZURE_ENDPOINT_NANO,
            api_key=config.AZURE_OPENAI_API_KEY_NANO
        )

    async def get_llm_questions(self, user_query: str, top_k: int = 3, lang: str = 'ru') -> Optional[List[str]]:
        """
        Генерирует уточняющие вопросы для поиска по базе законов.

        Parameters:
        user_query (str): Вопрос пользователя.
        top_k (int): Количество лучших вопросов для возврата.

        Returns:
        Optional[List[str]]: Список уточняющих вопросов или None в случае ошибки.
        """
        prompt = config.get_questions_prompt(user_query=user_query, lang=lang)
        try:
            response = await self.nano_client.responses.parse(
                model=config.AZURE_DEPLOYMENT_NANO,
                instructions="You are a legal assistant who helps people understand laws. Respond in the language of the context.",
                input=prompt,
                text_format=Queries
            )
            return [q.question for q in response.output_parsed.questions[:top_k]]
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None

    async def get_llm_response(self, user_query: str, top_results: List[Any], lang: str = 'ru') -> Optional[str]:
        """
        Получает развернутый ответ на вопрос пользователя на основе релевантных статей.

        Parameters:
        user_query (str): Вопрос пользователя.
        top_results (List[Any]): Список релевантных статей (словарей с ключами 'path' и 'text').

        Returns:
        Optional[str]: Ответ LLM или None в случае ошибки.
        """
        context = "\n\n".join([
            f"Source: {result['path']}\nText: {result['text']}"
            for result in top_results
        ])

        prompt = config.get_response_prompt(user_query=user_query, context=context, lang=lang)
        try:
            response = await self.nano_client.responses.create(
                model=config.AZURE_DEPLOYMENT_NANO,
                instructions="You are a legal assistant who helps people understand laws. Respond in the language of the context.",
                input=prompt
            )
            return response.output_text
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None
