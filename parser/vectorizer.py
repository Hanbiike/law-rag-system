"""
Vectorizer module for embedding legal document articles.

This module provides functionality to convert parsed articles into
vector embeddings using SentenceTransformer models.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Final, List, Optional, Union

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from parser.document_parser import Article, Language

# Disable tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"


@dataclass
class VectorizedArticle:
    """
    Data class representing an article with its embedding vector.
    
    Attributes:
        id: Unique identifier for the article.
        source_doc: Name of the source document.
        section: Section title.
        chapter: Chapter title.
        article_title: Article title.
        article_text: Full article text.
        vector: Embedding vector as numpy array.
        language: Language of the article.
    """
    
    id: int
    source_doc: str
    section: str
    chapter: str
    article_title: str
    article_text: str
    vector: np.ndarray
    language: Language = Language.RUSSIAN


class Vectorizer:
    """
    Vectorizer for converting articles to dense vector embeddings.
    
    Uses SentenceTransformer models to encode article text into
    high-dimensional vector representations suitable for semantic search.
    
    Attributes:
        model_name: Name of the SentenceTransformer model.
        device: Computation device (cuda or cpu).
        batch_size: Batch size for encoding.
    """
    
    DEFAULT_MODEL: Final[str] = "google/embeddinggemma-300m"
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: Optional[str] = None,
        batch_size: int = 32
    ) -> None:
        """
        Initialize the vectorizer with specified model.
        
        Parameters:
            model_name: Name of the SentenceTransformer model.
            device: Computation device ('cuda' or 'cpu'). Auto-detected if None.
            batch_size: Batch size for encoding operations.
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.batch_size = batch_size
        self._model: Optional[SentenceTransformer] = None
        
        print(f"Vectorizer initialized with device: {self.device}")
        if self.device == 'cuda':
            print(f"GPU: {torch.cuda.get_device_name(0)}")
    
    @property
    def model(self) -> SentenceTransformer:
        """
        Lazy load the SentenceTransformer model.
        
        Returns:
            SentenceTransformer: The loaded model.
        """
        if self._model is None:
            print(f"Loading model: {self.model_name}...")
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device
            )
            print("Model loaded successfully.")
        return self._model
    
    @property
    def embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            int: Dimension of embeddings (e.g., 768).
        """
        return self.model.get_sentence_embedding_dimension()
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Encode text(s) into embedding vectors.
        
        Parameters:
            texts: Single text or list of texts to encode.
            normalize: Whether to normalize embeddings.
            show_progress: Whether to show progress bar.
            
        Returns:
            np.ndarray: Embedding vector(s).
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            device=self.device,
            batch_size=self.batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=show_progress
        )
        
        return embeddings
    
    def vectorize_articles(
        self,
        articles: List[Article],
        start_id: int = 1,
        show_progress: bool = True
    ) -> List[VectorizedArticle]:
        """
        Convert articles to vectorized articles with embeddings.
        
        Parameters:
            articles: List of Article objects to vectorize.
            start_id: Starting ID for articles.
            show_progress: Whether to show progress updates.
            
        Returns:
            List[VectorizedArticle]: Articles with embeddings.
        """
        vectorized: List[VectorizedArticle] = []
        total = len(articles)
        
        # Extract all texts for batch processing
        texts = [article.text for article in articles]
        
        # Encode all texts at once for efficiency
        print(f"Vectorizing {total} articles...")
        embeddings = self.encode(texts, show_progress=show_progress)
        
        # Create VectorizedArticle objects
        for i, (article, embedding) in enumerate(zip(articles, embeddings)):
            vectorized.append(VectorizedArticle(
                id=start_id + i,
                source_doc=article.source_doc,
                section=article.section,
                chapter=article.chapter,
                article_title=article.title,
                article_text=article.text,
                vector=embedding,
                language=article.language
            ))
            
            if show_progress and (i + 1) % 100 == 0:
                print(f"   Vectorized {i + 1}/{total} articles")
        
        print(f"✅ Vectorization complete: {total} articles processed")
        return vectorized
    
    def save_to_json(
        self,
        articles: List[VectorizedArticle],
        output_path: str
    ) -> None:
        """
        Save vectorized articles to a JSON file.
        
        Parameters:
            articles: List of VectorizedArticle objects.
            output_path: Path to output JSON file.
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for article in articles:
                data = {
                    "id": article.id,
                    "source_doc": article.source_doc,
                    "section": article.section,
                    "chapter": article.chapter,
                    "article_title": article.article_title,
                    "article_text": article.article_text,
                    "vector": json.dumps(article.vector.tolist()),
                    "language": article.language.value
                }
                json_line = json.dumps(data, ensure_ascii=False)
                f.write(json_line + '\n')
        
        print(f"Saved {len(articles)} articles to {output_path}")
    
    @staticmethod
    def load_from_json(file_path: str) -> List[VectorizedArticle]:
        """
        Load vectorized articles from a JSON file.
        
        Parameters:
            file_path: Path to the JSON file.
            
        Returns:
            List[VectorizedArticle]: Loaded vectorized articles.
        """
        articles: List[VectorizedArticle] = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Handle trailing comma in JSON
                if line.endswith(','):
                    line = line[:-1]
                
                data = json.loads(line)
                lang_value = data.get("language", "ru")
                language = (Language.KYRGYZ if lang_value == "kg" 
                           else Language.RUSSIAN)
                
                vector_data = data["vector"]
                if isinstance(vector_data, str):
                    vector_data = json.loads(vector_data)
                
                articles.append(VectorizedArticle(
                    id=int(data["id"]),
                    source_doc=data["source_doc"],
                    section=data["section"],
                    chapter=data["chapter"],
                    article_title=data["article_title"],
                    article_text=data["article_text"],
                    vector=np.array(vector_data, dtype=np.float32),
                    language=language
                ))
        
        return articles
