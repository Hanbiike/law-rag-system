"""
Milvus vector database module for law search.

This module provides optimized vector similarity search using Milvus
for finding relevant law articles based on query embeddings.
"""
import logging
from typing import Any, Dict, Final, List, Optional

from pymilvus import MilvusClient

# Configure module logger
logger = logging.getLogger(__name__)

# Collection name constants
COLLECTION_RU: Final[str] = "law_collection"
COLLECTION_KG: Final[str] = "law_collection_kg"

# Output fields for search results
OUTPUT_FIELDS: Final[List[str]] = [
    "source_doc",
    "section",
    "chapter",
    "article_title",
    "article_text"
]


class MilvusLawSearcher:
    """
    High-performance law searcher using Milvus vector database.
    
    Features:
    - Singleton pattern for connection reuse
    - Optimized batch search
    - Multi-language support (Russian/Kyrgyz)
    - Efficient result deduplication
    """
    
    _instance: Optional["MilvusLawSearcher"] = None
    _client: Optional[MilvusClient] = None

    def __new__(cls, db_path: str = "milvus_law_rag.db") -> "MilvusLawSearcher":
        """
        Singleton pattern to reuse database connection.
        
        Parameters:
            db_path (str): Path to Milvus database file.
            
        Returns:
            MilvusLawSearcher: Singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "milvus_law_rag.db") -> None:
        """
        Initialize Milvus client connection.

        Parameters:
            db_path (str): Path to the Milvus database file.
        """
        if self._initialized:
            return
            
        self._client = MilvusClient(db_path)
        self._initialized = True

    def search_similar_laws(
        self,
        query_vectors: List[List[float]],
        top_k: int = 5,
        lang: str = 'ru'
    ) -> List[Dict[str, Any]]:
        """
        Search for most similar laws using cosine similarity.
        
        Performs batch search across query vectors and returns
        deduplicated, sorted results.

        Parameters:
            query_vectors (List[List[float]]): List of query embedding vectors.
            top_k (int): Number of top results per query. Defaults to 5.
            lang (str): Language code ('ru' or 'kg'). Defaults to 'ru'.

        Returns:
            List[Dict[str, Any]]: Structured search results with
                distance, path, and text fields. Sorted by relevance.
        """
        collection_name = COLLECTION_KG if lang == 'kg' else COLLECTION_RU

        try:
            results = self._client.search(
                collection_name=collection_name,
                data=query_vectors,
                limit=top_k,
                search_params={"metric_type": "COSINE"},
                output_fields=OUTPUT_FIELDS,
            )
        except Exception as e:
            logger.error("Milvus search error: %s", e)
            return []

        # Use dict for deduplication by article text
        seen_texts: Dict[str, Dict[str, Any]] = {}
        
        for query_results in results:
            for result in query_results:
                entity = result['entity']
                text = entity['article_text']
                
                # Keep highest scoring result for duplicate texts
                if text not in seen_texts or result['distance'] > seen_texts[text]['distance']:
                    seen_texts[text] = {
                        'distance': result['distance'],
                        'path': '\n'.join([
                            f"Source: {entity['source_doc']}",
                            f"Section: {entity['section']}",
                            f"Chapter: {entity['chapter']}",
                            f"Title: {entity['article_title']}"
                        ]),
                        'text': text
                    }

        # Sort by distance (highest similarity first)
        structured_results = sorted(
            seen_texts.values(),
            key=lambda x: x['distance'],
            reverse=True
        )

        return structured_results

