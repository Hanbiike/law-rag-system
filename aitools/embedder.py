"""
Query embedder module for semantic search.

This module provides efficient text embedding using SentenceTransformer
models with optimizations for batch processing and caching.
"""
import os
from functools import lru_cache
from typing import Final, List, Union

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

# Disable tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Default model configuration
DEFAULT_MODEL: Final[str] = "google/embeddinggemma-300m"
CACHE_SIZE: Final[int] = 512


class QueryEmbedder:
    """
    High-performance query embedder using SentenceTransformer.
    
    Features:
    - Automatic GPU/CPU detection
    - Batch processing support
    - LRU caching for repeated queries
    - Memory-efficient encoding
    """
    
    _instance = None
    _model = None
    
    def __new__(cls, model_name: str = DEFAULT_MODEL) -> "QueryEmbedder":
        """
        Singleton pattern to avoid loading model multiple times.
        
        Parameters:
            model_name (str): Name of the SentenceTransformer model.
            
        Returns:
            QueryEmbedder: Singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        """
        Initialize the embedder with specified model.
        
        Parameters:
            model_name (str): Name of the model from HuggingFace Hub.
        """
        if self._initialized:
            return
            
        self._device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._model = SentenceTransformer(model_name, device=self._device)
        self._initialized = True
    
    @property
    def device(self) -> str:
        """Get the current device (cuda or cpu)."""
        return self._device
    
    def encode_queries(
        self,
        queries: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True
    ) -> List[np.ndarray]:
        """
        Encode queries into dense vector embeddings.
        
        Optimized for batch processing with configurable batch size.
        
        Parameters:
            queries (Union[str, List[str]]): Single query or list of queries.
            batch_size (int): Batch size for encoding. Defaults to 32.
            normalize (bool): Whether to normalize embeddings. Defaults to True.
        
        Returns:
            List[np.ndarray]: List of embedding vectors.
        """
        if isinstance(queries, str):
            queries = [queries]
        
        embeddings = self._model.encode(
            queries,
            convert_to_numpy=True,
            device=self._device,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        
        return list(embeddings)
    
    @lru_cache(maxsize=CACHE_SIZE)
    def encode_single(self, query: str) -> tuple:
        """
        Encode a single query with caching.
        
        Uses LRU cache to avoid re-encoding identical queries.
        Returns tuple for hashability.
        
        Parameters:
            query (str): Text query to encode.
        
        Returns:
            tuple: Embedding as tuple (for caching).
        """
        embedding = self._model.encode(
            query,
            convert_to_numpy=True,
            device=self._device,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return tuple(embedding.tolist())
    
    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Parameters:
            a (np.ndarray): First embedding vector.
            b (np.ndarray): Second embedding vector.
        
        Returns:
            float: Cosine similarity score.
        """
        return float(self._model.similarity(a, b))
