import json
import mysql.connector
from mysql.connector import Error
import numpy as np

import embedder

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
    
connection = create_connection()

def close_connection():
    if connection and connection.is_connected():
        connection.close()
        print("MySQL connection closed")

def search_similar_laws(query_vector, top_k=5, lang='ru'):
    """Search for most similar laws using cosine similarity"""
    cursor = connection.cursor(dictionary=True)
    command = "SELECT source_doc, section, chapter, article_title, article_text, vector FROM vectorized_laws"
    if lang == 'kg':
        command = "SELECT source_doc, section, chapter, article_title, article_text, vector FROM vectorized_laws_kg"
    cursor.execute(command)
    
    results = []
    for row in cursor.fetchall():
        stored_vector = np.array(json.loads(row['vector']), dtype=np.float32)
        similarity = embedder.similarity(query_vector, stored_vector)
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

    