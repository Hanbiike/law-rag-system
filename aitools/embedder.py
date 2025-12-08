from sentence_transformers import SentenceTransformer
import os
import torch
import numpy as np
from typing import List, Union

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class QueryEmbedder:
    """
    Класс для кодирования запросов и вычисления косинусного сходства
    с использованием SentenceTransformer.
    """

    def __init__(self, model_name: str = "google/embeddinggemma-300m") -> None:
        """
        Инициализация модели SentenceTransformer.

        Parameters:
        model_name (str): Имя модели для загрузки из HuggingFace Hub.
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {self.device}")
        if self.device == 'cuda':
            print(f"GPU: {torch.cuda.get_device_name(0)}")
        # Загрузка модели на выбранное устройство
        self.model = SentenceTransformer(model_name, device=self.device)

    def encode_queries(self, queries: Union[str, List[str]]) -> List[np.ndarray]:
        """
        Кодирует список запросов в эмбеддинги.

        Parameters:
        queries (Union[str, List[str]]): Один или несколько текстовых запросов.

        Returns:
        List[np.ndarray]: Список эмбеддингов для каждого запроса.
        """
        if isinstance(queries, str):
            queries = [queries]
        tensors = self.model.encode(queries, convert_to_numpy=True, device=self.device)
        return [tensor for tensor in tensors]

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Вычисляет косинусное сходство между двумя векторами.

        Parameters:
        a (np.ndarray): Первый вектор.
        b (np.ndarray): Второй вектор.

        Returns:
        float: Значение косинусного сходства.
        """
        # Используем встроенный метод модели для вычисления сходства
        return self.model.similarity(a, b)
