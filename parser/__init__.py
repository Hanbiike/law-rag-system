"""
Parser module for processing legal documents.

This module provides OOP-based classes for parsing DOCX documents,
vectorizing text, and loading data into Milvus database.
"""

from parser.document_parser import DocumentParser, Language
from parser.vectorizer import Vectorizer
from parser.milvus_loader import MilvusLoader
from parser.pipeline import ParserPipeline

__all__ = [
    "DocumentParser",
    "Language",
    "Vectorizer",
    "MilvusLoader",
    "ParserPipeline",
]
