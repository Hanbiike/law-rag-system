"""
LLM Helper module for Azure OpenAI integration.

This module provides an optimized wrapper for Azure OpenAI API calls
using the new responses API. Includes connection pooling and error handling.
"""
import logging
from typing import Any, Final, List, Optional

from openai import AsyncAzureOpenAI
from pydantic import BaseModel

import confs.config as config

# Configure module logger
logger = logging.getLogger(__name__)

# System instruction constants to avoid recreating strings
LEGAL_ASSISTANT_INSTRUCTION: Final[str] = (
    "You are a legal assistant who helps people understand laws. "
    "Respond in the language of the context."
)
DATA_EXTRACTION_INSTRUCTION: Final[str] = (
    "You are an expert in extracting structured data. "
    "You will be given unstructured text from a legal document, "
    "and you must break it into items/paragraphs. "
    "Place the result into the specified structure. "
    "Respond in the language of the context."
)


class Query(BaseModel):
    """Model representing a single question."""
    
    question: str


class Queries(BaseModel):
    """Model representing a list of questions."""
    
    questions: List[Query]


class docQuery(BaseModel):
    """Model representing a single document paragraph."""
    
    paragraph: str


class docDataExtraction(BaseModel):
    """Model representing extracted document data."""
    
    points: List[docQuery]


class LLMHelper:
    """
    Optimized wrapper for Azure OpenAI LLM operations.
    
    Features:
    - Singleton pattern for connection reuse
    - Async operations for better performance
    - Structured error handling with logging
    - Memory-efficient context building
    """
    
    _instance: Optional["LLMHelper"] = None
    
    def __new__(cls) -> "LLMHelper":
        """
        Singleton pattern to reuse client connection.
        
        Returns:
            LLMHelper: Singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize Azure OpenAI client with configured credentials."""
        if self._initialized:
            return
            
        self.nano_client = AsyncAzureOpenAI(
            azure_deployment=config.AZURE_DEPLOYMENT_NANO,
            api_version=config.AZURE_API_VERSION_NANO,
            azure_endpoint=config.AZURE_ENDPOINT_NANO,
            api_key=config.AZURE_OPENAI_API_KEY_NANO
        )
        self._initialized = True

    async def get_llm_questions(
        self,
        user_query: str,
        top_k: int = 3,
        lang: str = 'ru'
    ) -> Optional[List[str]]:
        """
        Generate clarifying questions for law database search.
        
        Uses structured output parsing for reliable question extraction.

        Parameters:
            user_query (str): The user's original question.
            top_k (int): Maximum number of questions to return. Defaults to 3.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.

        Returns:
            Optional[List[str]]: List of generated questions or None on error.
        """
        prompt = config.get_questions_prompt(user_query=user_query, lang=lang)
        
        try:
            response = await self.nano_client.responses.parse(
                model=config.AZURE_DEPLOYMENT_NANO,
                instructions=LEGAL_ASSISTANT_INSTRUCTION,
                input=prompt,
                text_format=Queries
            )
            return [q.question for q in response.output_parsed.questions[:top_k]]
        except Exception as e:
            logger.error("Error generating LLM questions: %s", e)
            return None

    async def get_llm_response(
        self,
        user_query: str,
        top_results: List[Any],
        lang: str = 'ru'
    ) -> Optional[str]:
        """
        Generate detailed response based on relevant law articles.
        
        Builds context from search results and generates comprehensive answer.

        Parameters:
            user_query (str): The user's original question.
            top_results (List[Any]): List of relevant articles with 'path' and 'text'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.

        Returns:
            Optional[str]: Generated response text or None on error.
        """
        # Build context efficiently using join
        context_parts = [
            f"Source: {result['path']}\nText: {result['text']}"
            for result in top_results
        ]
        context = "\n\n".join(context_parts)

        prompt = config.get_response_prompt(
            user_query=user_query,
            context=context,
            lang=lang
        )
        
        try:
            response = await self.nano_client.responses.create(
                model=config.AZURE_DEPLOYMENT_NANO,
                instructions=LEGAL_ASSISTANT_INSTRUCTION,
                input=prompt
            )
            return response.output_text
        except Exception as e:
            logger.error("Error getting LLM response: %s", e)
            return None
        
    async def get_doc_data(
        self,
        document_base64: str
    ) -> Optional[List[str]]:
        """
        Extract structured data from a PDF document.
        
        Processes base64-encoded PDF and extracts paragraphs/items.

        Parameters:
            document_base64 (str): Base64-encoded PDF document.

        Returns:
            Optional[List[str]]: List of extracted paragraphs or None on error.
        """
        try:
            response = await self.nano_client.responses.parse(
                model=config.AZURE_DEPLOYMENT_NANO,
                instructions=DATA_EXTRACTION_INSTRUCTION,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Break it into items/paragraphs."
                            },
                            {
                                "type": "input_file",
                                "filename": "legal_document.pdf",
                                "file_data": f"data:application/pdf;base64,{document_base64}",
                            }
                        ],
                    },
                ],
                text_format=docDataExtraction
            )
            return [q.paragraph for q in response.output_parsed.points]
        except Exception as e:
            logger.error("Error extracting document data: %s", e)
            return None
