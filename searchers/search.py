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
    - Search mode: Direct vector search results without LLM
    - Document analysis support
    - Memory-efficient singleton components
    """
    
    # Search results header templates
    _SEARCH_HEADERS = {
        'ru': "🔍 **Найденные статьи:**\n\n",
        'kg': "🔍 **Табылган статьялар:**\n\n"
    }
    
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

    def _format_search_results(
        self,
        results: List[dict],
        lang: str = 'ru'
    ) -> str:
        """
        Format search results for display without LLM processing.
        
        Parameters:
            results (List[dict]): Search results with 'path' and 'text'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.
            
        Returns:
            str: Formatted search results string.
        """
        header = self._SEARCH_HEADERS.get(lang, self._SEARCH_HEADERS['ru'])
        
        formatted_parts = [header]
        for i, result in enumerate(results, 1):
            source = result.get('path', 'Неизвестный источник')
            text = result.get('text', '')
            
            formatted_parts.append(
                f"**{i}. {source}**\n"
                f"{text}\n\n"
                f"{'─' * 30}\n\n"
            )
        
        return ''.join(formatted_parts)

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
            type (str): Response type ('base', 'pro', or 'search'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.

        Returns:
            str: LLM response text or search results or empty string on error.
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
                # Base and Search modes: Direct query encoding
                query_vectors = self._embedder.encode_queries([query])

            # Search for relevant laws
            results = self._milvus.search_similar_laws(
                query_vectors,
                top_k=self._top_k,
                lang=lang
            )

            if not results:
                return ""

            # Search mode: Return formatted results without LLM
            if type == 'search':
                return self._format_search_results(results, lang)

            # Base/Pro mode: Generate response from LLM
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
        file_url: str,
        type: str = 'base',
        lang: str = 'ru'
    ) -> str:
        """
        Get RAG response from document as text string.

        Extracts document content, searches for relevant laws,
        and generates comprehensive response.

        Parameters:
            query (str): User's question about the document.
            file_url (str): Direct URL to the PDF document.
            type (str): Response type ('base' or 'pro'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.

        Returns:
            str: LLM response text or empty string on error.
        """
        try:
            # Extract document data
            doc_data = await self._llm.get_doc_data(file_url)
            if not doc_data:
                return ""

            # Combine query with document content
            user_input = config.concat_query_and_doc(query, doc_data)

            if type == 'pro':
                # Pro mode: For each paragraph, generate n questions and search
                # Result: paragraphs * n_questions * top_k articles
                all_results = []
                for paragraph in doc_data:
                    # Generate questions for this paragraph
                    llm_questions = await self._llm.get_llm_questions(
                        paragraph,
                        self._n_llm_questions,
                        lang=lang
                    )
                    if not llm_questions:
                        continue
                    
                    # Encode and search for each paragraph's questions
                    query_vectors = self._embedder.encode_queries(llm_questions)
                    paragraph_results = self._milvus.search_similar_laws(
                        query_vectors,
                        top_k=self._top_k,
                        lang=lang
                    )
                    if paragraph_results:
                        all_results.extend(paragraph_results)
                
                # Deduplicate results by text
                seen_texts = set()
                results = []
                for r in all_results:
                    if r['text'] not in seen_texts:
                        seen_texts.add(r['text'])
                        results.append(r)
            else:
                # Base mode: Encode document paragraphs directly
                query_vectors = self._embedder.encode_queries(doc_data)
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

    async def get_response_from_image_text(
        self,
        query: str,
        image_url: str,
        type: str = 'base',
        lang: str = 'ru'
    ) -> str:
        """
        Get RAG response from document screenshot/image as text string.

        Extracts document content from image, searches for relevant laws,
        and generates comprehensive response.

        Parameters:
            query (str): User's question about the document.
            image_url (str): Direct URL to the image.
            type (str): Response type ('base' or 'pro'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.

        Returns:
            str: LLM response text or empty string on error.
        """
        try:
            # Extract document data from image
            doc_data = await self._llm.get_image_data(image_url)
            if not doc_data:
                return ""

            # Combine query with document content
            user_input = config.concat_query_and_doc(query, doc_data)

            if type == 'pro':
                # Pro mode: For each paragraph, generate n questions and search
                # Result: paragraphs * n_questions * top_k articles
                all_results = []
                for paragraph in doc_data:
                    # Generate questions for this paragraph
                    llm_questions = await self._llm.get_llm_questions(
                        paragraph,
                        self._n_llm_questions,
                        lang=lang
                    )
                    if not llm_questions:
                        continue
                    
                    # Encode and search for each paragraph's questions
                    query_vectors = self._embedder.encode_queries(llm_questions)
                    paragraph_results = self._milvus.search_similar_laws(
                        query_vectors,
                        top_k=self._top_k,
                        lang=lang
                    )
                    if paragraph_results:
                        all_results.extend(paragraph_results)
                
                # Deduplicate results by text
                seen_texts = set()
                results = []
                for r in all_results:
                    if r['text'] not in seen_texts:
                        seen_texts.add(r['text'])
                        results.append(r)
            else:
                # Base mode: Encode document paragraphs directly
                query_vectors = self._embedder.encode_queries(doc_data)
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
            logger.error("Error in get_response_from_image_text: %s", e)
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
        file_url: str,
        type: str = 'base',
        lang: str = 'ru'
    ) -> None:
        """
        Run document search and print results to console.
        
        Primarily for debugging and CLI usage.

        Parameters:
            query (str): User's question about the document.
            file_url (str): Direct URL to the PDF document.
            type (str): Response type ('base' or 'pro'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.
        """
        response = await self.get_response_from_doc_text(
            query,
            file_url,
            type,
            lang
        )
        if response:
            print("\nLLM Response:")
            print(response)
        else:
            print("No response generated.")