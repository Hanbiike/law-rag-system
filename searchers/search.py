"""
Law RAG Search module.

This module provides optimized search functionality combining
vector similarity search with LLM-powered response generation.
"""
import logging
from typing import Final, List, Optional

import confs.config as config
import databases.milvus_db as milvus_db
import aitools.embedder as embedder
import aitools.llm as llm

# Configure module logger
logger = logging.getLogger(__name__)

# Default configuration constants
DEFAULT_TOP_K: Final[int] = 3
DEFAULT_LLM_QUESTIONS: Final[int] = 3


class ProLawRAGSearch:
    """
    High-performance law search with RAG capabilities.
    
    Features:
    - Base mode: Direct vector search + LLM response
    - Pro mode: LLM-generated queries + vector search + LLM response
    - Document analysis support
    - Memory-efficient singleton components
    """
    
    def __init__(
        self,
        top_k: int = DEFAULT_TOP_K,
        n_llm_questions: int = DEFAULT_LLM_QUESTIONS
    ) -> None:
        """
        Initialize RAG search with configurable parameters.
        
        Parameters:
            top_k (int): Number of top results to retrieve. Defaults to 3.
            n_llm_questions (int): Number of LLM questions for pro mode. Defaults to 3.
        """
        self._top_k = top_k
        self._n_llm_questions = n_llm_questions
        
        # Use singleton instances for efficiency
        self._embedder = embedder.QueryEmbedder()
        self._milvus = milvus_db.MilvusLawSearcher()
        self._llm = llm.LLMHelper()

    async def get_response_text(
        self,
        query: str,
        type: str = 'base',
        lang: str = 'ru'
    ) -> str:
        """
        Get RAG response as text string.

        Optimized for bot integration with efficient query handling.

        Parameters:
            query (str): User's question.
            type (str): Response type ('base' or 'pro'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.

        Returns:
            str: LLM response text or empty string on error.
        """
        try:
            if type == 'pro':
                # Pro mode: Generate clarifying questions first
                llm_questions = await self._llm.get_llm_questions(
                    query,
                    self._n_llm_questions,
                    lang=lang
                )
                if not llm_questions:
                    return ""
                
                query_vectors = self._embedder.encode_queries(llm_questions)
            else:
                # Base mode: Direct query encoding
                query_vectors = self._embedder.encode_queries([query])

            # Search for relevant laws
            results = self._milvus.search_similar_laws(
                query_vectors,
                top_k=self._top_k,
                lang=lang
            )

            if not results:
                return ""

            # Generate response from LLM
            response = await self._llm.get_llm_response(
                query,
                results,
                lang=lang
            )
            return response or ""

        except Exception as e:
            logger.error("Error in get_response_text: %s", e)
            return ""

    async def get_response_from_doc_text(
        self,
        query: str,
        document_base64: str,
        type: str = 'base',
        lang: str = 'ru'
    ) -> str:
        """
        Get RAG response from document as text string.

        Extracts document content, searches for relevant laws,
        and generates comprehensive response.

        Parameters:
            query (str): User's question about the document.
            document_base64 (str): Base64 encoded PDF document.
            type (str): Response type ('base' or 'pro'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.

        Returns:
            str: LLM response text or empty string on error.
        """
        try:
            # Extract document data
            doc_data = await self._llm.get_doc_data(document_base64)
            if not doc_data:
                return ""

            # Combine query with document content
            user_input = config.concat_query_and_doc(query, doc_data)

            if type == 'pro':
                # Pro mode: Generate questions from combined input
                llm_questions = await self._llm.get_llm_questions(
                    user_input,
                    self._n_llm_questions,
                    lang=lang
                )
                if not llm_questions:
                    return ""
                
                query_vectors = self._embedder.encode_queries(llm_questions)
            else:
                # Base mode: Encode document paragraphs directly
                query_vectors = self._embedder.encode_queries(doc_data)

            # Search for relevant laws
            results = self._milvus.search_similar_laws(
                query_vectors,
                top_k=self._top_k,
                lang=lang
            )

            if not results:
                return ""

            # Generate response from LLM
            response = await self._llm.get_llm_response(
                user_input,
                results,
                lang=lang
            )
            return response or ""

        except Exception as e:
            logger.error("Error in get_response_from_doc_text: %s", e)
            return ""

    async def get_response(
        self,
        query: str,
        type: str = 'base',
        lang: str = 'ru'
    ) -> None:
        """
        Run search and print results to console.
        
        Primarily for debugging and CLI usage.

        Parameters:
            query (str): User's question.
            type (str): Response type ('base' or 'pro'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.
        """
        response = await self.get_response_text(query, type, lang)
        if response:
            print("\nLLM Response:")
            print(response)
        else:
            print("No response generated.")

    async def get_response_from_doc(
        self,
        query: str,
        document_base64: str,
        type: str = 'base',
        lang: str = 'ru'
    ) -> None:
        """
        Run document search and print results to console.
        
        Primarily for debugging and CLI usage.

        Parameters:
            query (str): User's question about the document.
            document_base64 (str): Base64 encoded PDF document.
            type (str): Response type ('base' or 'pro'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.
        """
        response = await self.get_response_from_doc_text(
            query,
            document_base64,
            type,
            lang
        )
        if response:
            print("\nLLM Response:")
            print(response)
        else:
            print("No response generated.")