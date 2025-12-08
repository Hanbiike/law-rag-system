from pymilvus import MilvusClient
from typing import List, Dict, Any

class MilvusLawSearcher:
    """
    Класс для поиска наиболее похожих законов с использованием Milvus.
    """

    def __init__(self, db_path: str = "milvus_law_rag.db") -> None:
        """
        Инициализация клиента Milvus.

        Parameters:
        db_path (str): Путь к базе данных Milvus.
        """
        self.client = MilvusClient(db_path)

    def search_similar_laws(
        self,
        query_vectors: List[List[float]],
        top_k: int = 5,
        lang: str = 'ru'
    ) -> List[Dict[str, Any]]:
        """
        Поиск наиболее похожих законов по косинусному сходству.

        Parameters:
        query_vectors (List[List[float]]): Список векторов-запросов.
        top_k (int): Количество лучших результатов для каждого запроса.
        lang (str): Язык ('ru' или 'kg').

        Returns:
        List[Dict[str, Any]]: Список структурированных результатов поиска
                              с полями distance, path и text.
        """
        collection_name = 'law_collection'
        if lang == 'kg':
            collection_name = "law_collection_kg"

        results = self.client.search(
            collection_name=collection_name,
            data=query_vectors,
            limit=top_k,
            search_params={"metric_type": "COSINE"},
            output_fields=[
                "source_doc",
                'section',
                'chapter',
                'article_title',
                'article_text'
            ],
        )

        structured_results: List[Dict[str, Any]] = []
        # results — список списков: один список на каждый вектор запроса
        for query_results in results:
            for result in query_results:
                structured_results.append({
                    'distance': result['distance'],
                    'path': '\n'.join([
                        f"Source: {result['entity']['source_doc']}",
                        f"Section: {result['entity']['section']}",
                        f"Chapter: {result['entity']['chapter']}",
                        f"Title: {result['entity']['article_title']}"
                    ]),
                    'text': result['entity']['article_text']
                })
        # на всякий случай сортируем по distance
        structured_results.sort(key=lambda x: x['distance'], reverse=True)

        return structured_results

