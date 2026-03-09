"""
Law RAG Search module.

This module provides optimized search functionality combining
vector similarity search with LLM-powered response generation.
"""
import logging
from typing import AsyncGenerator, Final, List, Optional, Tuple

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
        lang: str = 'ru',
        previous_response_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Get RAG response as text string.

        Optimized for bot integration with efficient query handling.

        Parameters:
            query (str): User's question.
            type (str): Response type ('base', 'pro', or 'search'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.
            previous_response_id (Optional[str]): ID of the previous LLM response
                for chat history continuity. Defaults to None.

        Returns:
            Tuple[str, Optional[str]]: (response_text, response_id).
                response_text is empty string on error or no results.
                response_id is None for search mode or on error.
        """
        try:
            if type == 'search':
                # Search mode: Direct query encoding, no LLM pre-processing
                query_vectors = self._embedder.encode_queries([query])
            else:
                # Base mode: 1 expanded query; Pro mode: n queries.
                # A single structured-output call decides whether RAG is
                # needed at all and returns the expanded search questions.
                n = 1 if type == 'base' else self._n_llm_questions
                decision = await self._llm.get_rag_decision(
                    query, n_questions=n, lang=lang
                )
                if not decision:
                    return "", None

                if not decision.is_rag_needed:
                    # No RAG needed — answer directly without vector search
                    return await self._llm.get_llm_direct_response(
                        query,
                        lang=lang,
                        previous_response_id=previous_response_id
                    )

                search_questions = [q.question for q in decision.questions]
                if not search_questions:
                    return "", None
                query_vectors = self._embedder.encode_queries(search_questions)

            # Search for relevant laws
            results = self._milvus.search_similar_laws(
                query_vectors,
                top_k=self._top_k,
                lang=lang
            )

            if not results:
                return "", None

            # Search mode: Return formatted results without LLM
            if type == 'search':
                return self._format_search_results(results, lang), None

            # Base/Pro mode: Generate response from LLM
            text, response_id = await self._llm.get_llm_response(
                query,
                results,
                lang=lang,
                previous_response_id=previous_response_id
            )
            return text or "", response_id

        except Exception as e:
            logger.error("Error in get_response_text: %s", e)
            return "", None

    async def get_response_from_doc_text(
        self,
        query: str,
        file_url: str,
        type: str = 'base',
        lang: str = 'ru',
        previous_response_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Get RAG response from document as text string.

        Extracts document content, searches for relevant laws,
        and generates comprehensive response.

        Parameters:
            query (str): User's question about the document.
            file_url (str): Direct URL to the PDF document.
            type (str): Response type ('base' or 'pro'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.
            previous_response_id (Optional[str]): ID of the previous LLM response
                for chat history continuity. Defaults to None.

        Returns:
            Tuple[str, Optional[str]]: (response_text, response_id).
        """
        try:
            # Extract document data
            doc_data = await self._llm.get_doc_data(file_url)
            if not doc_data:
                return "", None

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
                return "", None

            # Generate response from LLM
            text, response_id = await self._llm.get_llm_response(
                user_input,
                results,
                lang=lang,
                previous_response_id=previous_response_id
            )
            return text or "", response_id

        except Exception as e:
            logger.error("Error in get_response_from_doc_text: %s", e)
            return "", None

    async def get_response_from_image_text(
        self,
        query: str,
        image_url: str,
        type: str = 'base',
        lang: str = 'ru',
        previous_response_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Get RAG response from document screenshot/image as text string.

        Extracts document content from image, searches for relevant laws,
        and generates comprehensive response.

        Parameters:
            query (str): User's question about the document.
            image_url (str): Direct URL to the image.
            type (str): Response type ('base' or 'pro'). Defaults to 'base'.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.
            previous_response_id (Optional[str]): ID of the previous LLM response
                for chat history continuity. Defaults to None.

        Returns:
            Tuple[str, Optional[str]]: (response_text, response_id).
        """
        try:
            # Extract document data from image
            doc_data = await self._llm.get_image_data(image_url)
            if not doc_data:
                return "", None

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
                return "", None

            # Generate response from LLM
            text, response_id = await self._llm.get_llm_response(
                user_input,
                results,
                lang=lang,
                previous_response_id=previous_response_id
            )
            return text or "", response_id

        except Exception as e:
            logger.error("Error in get_response_from_image_text: %s", e)
            return "", None

    # ------------------------------------------------------------------
    # Streaming methods (token-by-token SSE)
    # ------------------------------------------------------------------

    async def stream_response_text(
        self,
        query: str,
        type: str = 'base',
        lang: str = 'ru',
        previous_response_id: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Stream RAG response token by token for a plain-text query.

        Yields delta dicts for each token and a final 'done' or 'error' dict.
        Search mode yields the full formatted result as a single delta followed
        by 'done' (no LLM streaming needed).

        Parameters:
            query (str): User's question.
            type (str): 'base', 'pro', or 'search'. Defaults to 'base'.
            lang (str): 'ru' or 'kg'. Defaults to 'ru'.
            previous_response_id (Optional[str]): Previous response ID for chat history.

        Yields:
            dict: {"type": "delta", "content": str} |
                  {"type": "done",  "response_id": str | None} |
                  {"type": "error", "message": str}
        """
        try:
            if type == 'search':
                # Search mode: Direct query encoding, no LLM pre-processing
                query_vectors = self._embedder.encode_queries([query])
            else:
                # Base mode: 1 expanded query; Pro mode: n queries.
                # A single structured-output call decides whether RAG is
                # needed at all and returns the expanded search questions.
                n = 1 if type == 'base' else self._n_llm_questions
                decision = await self._llm.get_rag_decision(
                    query, n_questions=n, lang=lang
                )
                if not decision:
                    yield {"type": "error", "message": "Failed to evaluate query"}
                    return

                if not decision.is_rag_needed:
                    # No RAG needed — stream answer directly without
                    # touching the vector DB
                    async for chunk in self._llm.stream_llm_direct_response(
                        query,
                        lang=lang,
                        previous_response_id=previous_response_id
                    ):
                        yield chunk
                    return

                search_questions = [q.question for q in decision.questions]
                if not search_questions:
                    yield {"type": "error", "message": "No search queries generated"}
                    return
                query_vectors = self._embedder.encode_queries(search_questions)

            results = self._milvus.search_similar_laws(
                query_vectors, top_k=self._top_k, lang=lang
            )
            if not results:
                yield {"type": "error", "message": "No relevant articles found"}
                return

            if type == 'search':
                # Search mode: single delta with formatted articles, no LLM
                yield {"type": "delta", "content": self._format_search_results(results, lang)}
                yield {"type": "done", "response_id": None}
                return

            async for chunk in self._llm.stream_llm_response(
                query, results, lang=lang, previous_response_id=previous_response_id
            ):
                yield chunk

        except Exception as e:
            logger.error("Error in stream_response_text: %s", e)
            yield {"type": "error", "message": str(e)}

    async def stream_response_from_doc_text(
        self,
        query: str,
        file_url: str,
        type: str = 'base',
        lang: str = 'ru',
        previous_response_id: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Stream RAG response token by token for a PDF document query.

        Extracts document content and searches for relevant laws synchronously,
        then streams the LLM answer.

        Parameters:
            query (str): User's question about the document.
            file_url (str): Direct URL to the PDF document.
            type (str): 'base' or 'pro'. Defaults to 'base'.
            lang (str): 'ru' or 'kg'. Defaults to 'ru'.
            previous_response_id (Optional[str]): Previous response ID for chat history.

        Yields:
            dict: {"type": "delta"|"done"|"error", ...}
        """
        try:
            doc_data = await self._llm.get_doc_data(file_url)
            if not doc_data:
                yield {"type": "error", "message": "Failed to extract document data"}
                return

            user_input = config.concat_query_and_doc(query, doc_data)

            if type == 'pro':
                all_results: List[dict] = []
                for paragraph in doc_data:
                    llm_questions = await self._llm.get_llm_questions(
                        paragraph, self._n_llm_questions, lang=lang
                    )
                    if not llm_questions:
                        continue
                    query_vectors = self._embedder.encode_queries(llm_questions)
                    paragraph_results = self._milvus.search_similar_laws(
                        query_vectors, top_k=self._top_k, lang=lang
                    )
                    if paragraph_results:
                        all_results.extend(paragraph_results)

                seen_texts: set = set()
                results: List[dict] = []
                for r in all_results:
                    if r['text'] not in seen_texts:
                        seen_texts.add(r['text'])
                        results.append(r)
            else:
                query_vectors = self._embedder.encode_queries(doc_data)
                results = self._milvus.search_similar_laws(
                    query_vectors, top_k=self._top_k, lang=lang
                )

            if not results:
                yield {"type": "error", "message": "No relevant articles found"}
                return

            async for chunk in self._llm.stream_llm_response(
                user_input, results, lang=lang, previous_response_id=previous_response_id
            ):
                yield chunk

        except Exception as e:
            logger.error("Error in stream_response_from_doc_text: %s", e)
            yield {"type": "error", "message": str(e)}

    async def stream_response_from_image_text(
        self,
        query: str,
        image_url: str,
        type: str = 'base',
        lang: str = 'ru',
        previous_response_id: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Stream RAG response token by token for a document image query.

        Extracts text from the image and searches for relevant laws synchronously,
        then streams the LLM answer.

        Parameters:
            query (str): User's question about the image.
            image_url (str): Direct URL to the image (JPEG/PNG/GIF/WebP).
            type (str): 'base' or 'pro'. Defaults to 'base'.
            lang (str): 'ru' or 'kg'. Defaults to 'ru'.
            previous_response_id (Optional[str]): Previous response ID for chat history.

        Yields:
            dict: {"type": "delta"|"done"|"error", ...}
        """
        try:
            doc_data = await self._llm.get_image_data(image_url)
            if not doc_data:
                yield {"type": "error", "message": "Failed to extract image data"}
                return

            user_input = config.concat_query_and_doc(query, doc_data)

            if type == 'pro':
                all_results_img: List[dict] = []
                for paragraph in doc_data:
                    llm_questions = await self._llm.get_llm_questions(
                        paragraph, self._n_llm_questions, lang=lang
                    )
                    if not llm_questions:
                        continue
                    query_vectors = self._embedder.encode_queries(llm_questions)
                    paragraph_results = self._milvus.search_similar_laws(
                        query_vectors, top_k=self._top_k, lang=lang
                    )
                    if paragraph_results:
                        all_results_img.extend(paragraph_results)

                seen_texts_img: set = set()
                results_img: List[dict] = []
                for r in all_results_img:
                    if r['text'] not in seen_texts_img:
                        seen_texts_img.add(r['text'])
                        results_img.append(r)
                results = results_img
            else:
                query_vectors = self._embedder.encode_queries(doc_data)
                results = self._milvus.search_similar_laws(
                    query_vectors, top_k=self._top_k, lang=lang
                )

            if not results:
                yield {"type": "error", "message": "No relevant articles found"}
                return

            async for chunk in self._llm.stream_llm_response(
                user_input, results, lang=lang, previous_response_id=previous_response_id
            ):
                yield chunk

        except Exception as e:
            logger.error("Error in stream_response_from_image_text: %s", e)
            yield {"type": "error", "message": str(e)}

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
        response, _ = await self.get_response_text(query, type, lang)
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
        response, _ = await self.get_response_from_doc_text(
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