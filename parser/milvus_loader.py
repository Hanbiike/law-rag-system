"""
Milvus database loader module for storing vectorized articles.

This module provides functionality to load vectorized articles into
Milvus vector database for efficient similarity search.
"""

import json
from typing import Dict, Final, List, Optional

import numpy as np
from pymilvus import MilvusClient

from parser.document_parser import Language
from parser.vectorizer import VectorizedArticle


class MilvusLoader:
    """
    Loader for storing vectorized articles in Milvus database.
    
    Handles collection creation, data insertion, and loading
    for both Russian and Kyrgyz language collections.
    
    Attributes:
        db_path: Path to the Milvus database file.
        client: MilvusClient instance.
        dimension: Vector embedding dimension.
        metric_type: Distance metric for similarity search.
    """
    
    # Collection names for different languages
    COLLECTION_RU: Final[str] = "law_collection"
    COLLECTION_KG: Final[str] = "law_collection_kg"
    
    # Default configuration
    DEFAULT_DB_PATH: Final[str] = "milvus_law_rag.db"
    DEFAULT_DIMENSION: Final[int] = 768
    DEFAULT_METRIC: Final[str] = "COSINE"
    
    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        dimension: int = DEFAULT_DIMENSION,
        metric_type: str = DEFAULT_METRIC
    ) -> None:
        """
        Initialize the Milvus loader.
        
        Parameters:
            db_path: Path to the Milvus database file.
            dimension: Dimension of embedding vectors.
            metric_type: Distance metric ('COSINE', 'L2', 'IP').
        """
        self.db_path = db_path
        self.dimension = dimension
        self.metric_type = metric_type
        self._client: Optional[MilvusClient] = None
    
    @property
    def client(self) -> MilvusClient:
        """
        Lazy-load the Milvus client.
        
        Returns:
            MilvusClient: Connected client instance.
        """
        if self._client is None:
            self._client = MilvusClient(self.db_path)
            print(f"Connected to Milvus database: {self.db_path}")
        return self._client
    
    def get_collection_name(self, language: Language) -> str:
        """
        Get the collection name for a language.
        
        Parameters:
            language: Target language.
            
        Returns:
            str: Collection name for the language.
        """
        if language == Language.KYRGYZ:
            return self.COLLECTION_KG
        return self.COLLECTION_RU
    
    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists.
        
        Parameters:
            collection_name: Name of the collection.
            
        Returns:
            bool: True if collection exists.
        """
        return self.client.has_collection(collection_name=collection_name)
    
    def drop_collection(self, collection_name: str) -> None:
        """
        Drop a collection if it exists.
        
        Parameters:
            collection_name: Name of the collection to drop.
        """
        if self.collection_exists(collection_name):
            self.client.drop_collection(collection_name=collection_name)
            print(f"Dropped collection: {collection_name}")
    
    def create_collection(
        self,
        collection_name: str,
        drop_existing: bool = True
    ) -> None:
        """
        Create a new collection for storing vectors.
        
        Parameters:
            collection_name: Name of the collection to create.
            drop_existing: Whether to drop existing collection.
        """
        if drop_existing:
            self.drop_collection(collection_name)
        
        self.client.create_collection(
            collection_name=collection_name,
            dimension=self.dimension,
            metric_type=self.metric_type
        )
        print(f"Created collection: {collection_name} "
              f"(dim={self.dimension}, metric={self.metric_type})")
    
    def insert_articles(
        self,
        collection_name: str,
        articles: List[VectorizedArticle]
    ) -> None:
        """
        Insert vectorized articles into a collection.
        
        Parameters:
            collection_name: Target collection name.
            articles: List of vectorized articles to insert.
        """
        if not articles:
            print("No articles to insert.")
            return
        
        data = []
        for article in articles:
            data.append({
                "id": article.id,
                "vector": article.vector.astype(np.float32),
                "source_doc": article.source_doc,
                "section": article.section,
                "chapter": article.chapter,
                "article_title": article.article_title,
                "article_text": article.article_text
            })
        
        self.client.insert(
            collection_name=collection_name,
            data=data
        )
        print(f"Inserted {len(articles)} articles into {collection_name}")
    
    def load_collection(self, collection_name: str) -> None:
        """
        Load a collection into memory for searching.
        
        Parameters:
            collection_name: Name of the collection to load.
        """
        self.client.load_collection(collection_name)
        print(f"Loaded collection: {collection_name}")
    
    def describe_collection(self, collection_name: str) -> Dict:
        """
        Get collection statistics and information.
        
        Parameters:
            collection_name: Name of the collection.
            
        Returns:
            Dict: Collection description.
        """
        return self.client.describe_collection(collection_name)
    
    def setup_language_collection(
        self,
        language: Language,
        articles: List[VectorizedArticle],
        drop_existing: bool = True
    ) -> None:
        """
        Set up a complete collection for a language.
        
        Creates the collection, inserts articles, and loads for searching.
        
        Parameters:
            language: Target language.
            articles: Vectorized articles to insert.
            drop_existing: Whether to drop existing collection.
        """
        collection_name = self.get_collection_name(language)
        
        self.create_collection(collection_name, drop_existing)
        self.insert_articles(collection_name, articles)
        self.load_collection(collection_name)
        
        # Print collection info
        info = self.describe_collection(collection_name)
        print(f"Collection {collection_name} ready: {info}")
    
    def setup_all_collections(
        self,
        ru_articles: Optional[List[VectorizedArticle]] = None,
        kg_articles: Optional[List[VectorizedArticle]] = None,
        drop_existing: bool = True
    ) -> None:
        """
        Set up collections for all languages.
        
        Parameters:
            ru_articles: Russian language articles.
            kg_articles: Kyrgyz language articles.
            drop_existing: Whether to drop existing collections.
        """
        if ru_articles:
            self.setup_language_collection(
                Language.RUSSIAN,
                ru_articles,
                drop_existing
            )
        
        if kg_articles:
            self.setup_language_collection(
                Language.KYRGYZ,
                kg_articles,
                drop_existing
            )
        
        print("\n✅ All collections set up successfully!")
    
    def load_from_json_file(
        self,
        file_path: str,
        language: Language,
        drop_existing: bool = True
    ) -> None:
        """
        Load articles from a JSON file into a collection.
        
        Parameters:
            file_path: Path to the JSON file with vectorized articles.
            language: Target language.
            drop_existing: Whether to drop existing collection.
        """
        print(f"Loading articles from: {file_path}")
        
        data = []
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.readlines()
        
        for line in raw:
            line = line.strip()
            if not line:
                continue
            
            # Handle trailing comma
            if line.endswith(','):
                line = line[:-1]
            
            json_obj = json.loads(line)
            json_obj['id'] = int(json_obj['id'])
            
            vector_data = json_obj['vector']
            if isinstance(vector_data, str):
                vector_data = json.loads(vector_data)
            json_obj['vector'] = np.array(vector_data, dtype=np.float32)
            
            data.append({
                "id": json_obj['id'],
                "vector": json_obj['vector'],
                "source_doc": json_obj['source_doc'],
                "section": json_obj['section'],
                "chapter": json_obj['chapter'],
                "article_title": json_obj['article_title'],
                "article_text": json_obj['article_text']
            })
        
        collection_name = self.get_collection_name(language)
        self.create_collection(collection_name, drop_existing)
        
        self.client.insert(
            collection_name=collection_name,
            data=data
        )
        print(f"Inserted {len(data)} articles from file")
        
        self.load_collection(collection_name)
    
    def query(
        self,
        collection_name: str,
        output_fields: List[str],
        limit: int = 10
    ) -> List[Dict]:
        """
        Query records from a collection.
        
        Parameters:
            collection_name: Name of the collection.
            output_fields: Fields to retrieve.
            limit: Maximum number of records.
            
        Returns:
            List[Dict]: Query results.
        """
        return self.client.query(
            collection_name=collection_name,
            output_fields=output_fields,
            limit=limit
        )
    
    def close(self) -> None:
        """Close the Milvus client connection."""
        if self._client is not None:
            self._client = None
            print("Milvus connection closed")
