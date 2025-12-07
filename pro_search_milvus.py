import asyncio

import databases.milvus_db as milvus_db
import aitools.llm as llm
import aitools.embedder as embedder

async def main():
    user_input = input("Enter text to vectorize: ")
    # Get enhanced questions from LLM
    llm_questions = await llm.get_llm_questions(user_input, 3)

    print("\nGenerated Queries from LLM:")
    for i, query in enumerate(llm_questions, 1):
        print(f"{i}. {query}")

    query_vectors = embedder.encode_queries(llm_questions)
    results = milvus_db.search_similar_laws(query_vectors, top_k=3)
        
    print(f"\nTop {len(results)} most similar laws:\n")
    for result in results:
        print(result)
        print()
        
    # Get LLM response
    print("\n" + "="*80)
    print("Получение ответа от LLM...")
    print("="*80 + "\n")
    
    llm_response = await llm.get_llm_response(user_input, results)
    if llm_response:
        print("LLM Ответ:")
        print(llm_response)

# Remove the synchronous code and replace with async execution
if __name__ == "__main__":
    asyncio.run(main())


