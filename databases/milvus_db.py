from pymilvus import MilvusClient
from typing import List, Dict, Any

client = MilvusClient("milvus_law_rag.db")


def search_similar_laws(
    query_vectors: List[List[float]], 
    top_k: int = 5, 
    lang: str = 'ru'
) -> List[Dict[str, Any]]:
    """
    Search for most similar laws using cosine similarity.
    
    Parameters:
    query_vectors (List[List[float]]): List of query embedding vectors
    top_k (int): Number of top results to return per query
    lang (str): Language code ('ru' or 'kg')
    
    Returns:
    List[Dict[str, Any]]: List of structured search results with 
                          distance, path, and text fields
    """
    collection_name = 'law_collection'
    if lang == 'kg':
        collection_name = "law_collection_kg"

    results = client.search(
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

    structured_results = []
    # results is a list of lists - one list per query vector
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
        
    return structured_results

