import asyncio
import databases.milvus_db as milvus_db
import aitools.llm as llm
import aitools.embedder as embedder
import confs.config as config
from typing import List

class ProLawRAGSearch:
    """
    Класс для поиска похожих законов и получения ответа LLM по пользовательскому запросу.
    """
    def __init__(self, top_k: int = 3, n_llm_questions: int = 3) -> None:
        """
        Инициализация параметров поиска.
        
        Parameters:
        top_k (int): Количество наиболее похожих законов для вывода.
        n_llm_questions (int): Количество уточняющих вопросов, генерируемых LLM.
        """
        self.top_k = top_k
        self.n_llm_questions = n_llm_questions
        self.embedder = embedder.QueryEmbedder()
        self.milvus_db = milvus_db.MilvusLawSearcher()
        self.llm = llm.LLMHelper()

    async def get_response(self, query: str, type: str = 'base', lang: str = 'ru') -> None:
        """
        Запуск основного процесса поиска и получения ответа LLM.
        """
        if type == 'base':
            user_input = query

            query_vectors = self.embedder.encode_queries([user_input])

            results = self.milvus_db.search_similar_laws(query_vectors, top_k=self.top_k, lang=lang)

            print(f"\nTop {len(results)} most similar laws:\n")
            for result in results:
                print(result)
                print()

            # Получение ответа от LLM
            print("\n" + "="*80)
            print("Получение ответа от LLM...")
            print("="*80 + "\n")

            llm_response = await self.llm.get_llm_response(user_input, results, lang=lang)
            if llm_response:
                print("LLM Ответ:")
                print(llm_response)

        elif type == 'pro':
            user_input = query
            # Получение уточняющих вопросов от LLM
            llm_questions: List[str] = await self.llm.get_llm_questions(user_input, self.n_llm_questions, lang=lang)

            print("\nGenerated Queries from LLM:")
            for i, query in enumerate(llm_questions, 1):
                print(f"{i}. {query}")

            query_vectors = self.embedder.encode_queries(llm_questions)
            results = self.milvus_db.search_similar_laws(query_vectors, top_k=self.top_k, lang=lang)

            print(f"\nTop {len(results)} most similar laws:\n")
            for result in results:
                print(result)
                print()

            # Получение ответа от LLM
            print("\n" + "="*80)
            print("Получение ответа от LLM...")
            print("="*80 + "\n")

            llm_response = await self.llm.get_llm_response(user_input, results, lang=lang)
            if llm_response:
                print("LLM Ответ:")
                print(llm_response)

    
    async def get_response_from_doc(self, query: str, document_base64: str, type: str = 'base', lang: str = 'ru') -> None:
        """
        Запуск основного процесса поиска и получения ответа LLM.
        """
        if type == 'base':
            doc_data = await self.llm.get_doc_data(document_base64=document_base64)

            user_input = config.concat_query_and_doc(query, doc_data)

            print("\nDocument Data Extracted:")
            for i, item in enumerate(doc_data, 1):
                print(f"{i}. {item}")

            query_vectors = self.embedder.encode_queries(doc_data)

            results = self.milvus_db.search_similar_laws(query_vectors, top_k=self.top_k, lang=lang)

            print(f"\nTop {len(results)} most similar laws:\n")
            for result in results:
                print(result)
                print()

            # Получение ответа от LLM
            print("\n" + "="*80)
            print("Получение ответа от LLM...")
            print("="*80 + "\n")

            llm_response = await self.llm.get_llm_response(user_input, results, lang=lang)
            if llm_response:
                print("LLM Ответ:")
                print(llm_response)

        elif type == 'pro':
            doc_data = await self.llm.get_doc_data(document_base64=document_base64)

            user_input = config.concat_query_and_doc(query, doc_data)
            # Получение уточняющих вопросов от LLM
            llm_questions: List[str] = await self.llm.get_llm_questions(user_input, self.n_llm_questions, lang=lang)

            print("\nGenerated Queries from LLM:")
            for i, query in enumerate(llm_questions, 1):
                print(f"{i}. {query}")

            query_vectors = self.embedder.encode_queries(llm_questions)
            results = self.milvus_db.search_similar_laws(query_vectors, top_k=self.top_k, lang=lang)

            print(f"\nTop {len(results)} most similar laws:\n")
            for result in results:
                print(result)
                print()

            # Получение ответа от LLM
            print("\n" + "="*80)
            print("Получение ответа от LLM...")
            print("="*80 + "\n")

            llm_response = await self.llm.get_llm_response(user_input, results, lang=lang)
            if llm_response:
                print("LLM Ответ:")
                print(llm_response)

# if __name__ == "__main__":
#     searcher = LawRAGSearch()
#     asyncio.run(searcher.get_response("Какие права имеет работник при увольнении по сокращению штатов?"))