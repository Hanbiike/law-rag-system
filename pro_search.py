import asyncio

import db
import llm
import embedder

async def main():
    user_input = input("Enter text to vectorize: ")
    # Get enhanced questions from LLM
    llm_questions = await llm.get_llm_questions(user_input)

    print("\nGenerated Queries from LLM:")
    for i, query in enumerate(llm_questions.questions, 1):
        print(f"{i}. {query.question}")

    results = []

    for i, query in enumerate(llm_questions.questions, 1):
        print(f"\nProcessing Query {i}: {query.question}")
        query_vector = embedder.encode_query(query.question)
    
        # Perform search
        results.extend(db.search_similar_laws(query_vector, top_k=3))
        
        print(f"\nTop {len(results)} most similar laws:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. Similarity: {result['similarity']:.4f}")
            print(f"   Source: {result['source_doc']}")
            print(f"   Title: {result['title']}")
            print(f"   Text: {result['text'][:200]}...")
            print()
            
        # Get LLM response
        print("\n" + "="*80)
        print("Получение ответа от LLM...")
        print("="*80 + "\n")
        
        llm_response = await llm.get_llm_response(user_input, results)
        if llm_response:
            print("LLM Ответ:")
            print(llm_response)
        
        db.close_connection()

# Remove the synchronous code and replace with async execution
if __name__ == "__main__":
    asyncio.run(main())


