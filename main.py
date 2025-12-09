"""
Main entry point for Law RAG System CLI.

This script provides command-line interface for testing
the RAG search functionality.
"""
import asyncio
import base64
import sys
from pathlib import Path

from searchers.search import ProLawRAGSearch


def main() -> None:
    """
    Run example RAG search queries.
    
    Demonstrates both text and document-based search capabilities.
    """
    searcher = ProLawRAGSearch(top_k=1, n_llm_questions=2)
    
    # Check if document exists for testing
    doc_path = Path("pril-9-regl.pdf")
    
    if doc_path.exists():
        with open(doc_path, "rb") as f:
            document_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        asyncio.run(searcher.get_response_from_doc(
            query="Законен ли данный документ?",
            document_base64=document_base64,
            type='pro',
            lang='ru'
        ))
    else:
        # Fallback to text query
        asyncio.run(searcher.get_response(
            query="Какие права имеет работник при увольнении?",
            type='pro',
            lang='ru'
        ))


if __name__ == "__main__":
    main()