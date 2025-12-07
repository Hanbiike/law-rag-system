import json
from sentence_transformers import SentenceTransformer
import os
import mysql.connector
from mysql.connector import Error
import torch
import numpy as np
import asyncio
from openai import AsyncAzureOpenAI
import config

client = AsyncAzureOpenAI(azure_deployment=config.AZURE_DEPLOYMENT, api_version=config.AZURE_API_VERSION, azure_endpoint=config.AZURE_ENDPOINT, api_key=config.AZURE_OPENAI_API_KEY)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Check if CUDA is available
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")
if device == 'cuda':
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Download from the 🤗 Hub and load to CUDA if available
model = SentenceTransformer("google/embeddinggemma-300m", device=device)

# MySQL connection settings
db_config = {
    'host': 'localhost',
    'user': 'root',  # Change to your MySQL user
    'password': 'root',  # Change to your MySQL password
    'database': 'law_rag_db',  # Change to your database name
    'port': 8889
}

def create_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Successfully connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def search_similar_laws(connection, query_vector, top_k=5):
    """Search for most similar laws using cosine similarity"""
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, source_doc, title, text, vector FROM vectorized_laws")
    
    results = []
    for row in cursor.fetchall():
        stored_vector = np.array(json.loads(row['vector']), dtype=np.float32)
        similarity = model.similarity(query_vector, stored_vector)
        results.append({
            'id': row['id'],
            'source_doc': row['source_doc'],
            'title': row['title'],
            'text': row['text'],
            'similarity': similarity.item()
        })
    
    # Sort by similarity (descending) and return top_k
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]

async def get_llm_response(user_query, top_results):
    """Send top results to LLM for analysis"""
    # Prepare context from top 3 results
    context = "\n\n".join([
        f"Документ {i+1} (Similarity: {result['similarity']:.4f}):\n"
        f"Источник: {result['source_doc']}\n"
        f"Название: {result['title']}\n"
        f"Текст: {result['text']}"
        for i, result in enumerate(top_results[:3])
    ])
    
    prompt = f"""
На основе следующих релевантных статей закона, ответь на вопрос пользователя.

Вопрос: {user_query}

Релевантные статьи:
{context}

Пожалуйста, дай подробный ответ, ссылаясь на конкретные статьи."""

    try:
        response = await client.responses.create(
            model=config.AZURE_DEPLOYMENT,
            instructions="Ты юридический помощник, который помогает людям понимать законы.",
            input=prompt
        )
        return response.output_text
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None

async def main():
    user_input = input("Enter text to vectorize: ")
    vector = model.encode(user_input)
    
    # Perform search
    connection = create_connection()
    if connection:
        results = search_similar_laws(connection, vector, top_k=5)
        
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
        
        llm_response = await get_llm_response(user_input, results)
        if llm_response:
            print("LLM Ответ:")
            print(llm_response)
        
        connection.close()
    else:
        print("Failed to connect to database")

# Remove the synchronous code and replace with async execution
if __name__ == "__main__":
    asyncio.run(main())


