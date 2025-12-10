"""
Document parser module for extracting articles from DOCX files.

This module provides a language-agnostic document parser that
supports Russian and Kyrgyz legal documents with configurable
patterns for article, section, and chapter detection.
"""

import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Final, List, Optional, Pattern

from docx import Document


class Language(Enum):
    """Supported languages for document parsing."""
    
    RUSSIAN = "ru"
    KYRGYZ = "kg"


@dataclass
class Article:
    """
    Data class representing a parsed article.
    
    Attributes:
        source_doc: Name of the source document file.
        section: Section title (e.g., "РАЗДЕЛ I").
        chapter: Chapter title (e.g., "ГЛАВА 1").
        title: Article title.
        text: Full article text content.
        language: Language of the article.
    """
    
    source_doc: str
    section: str
    chapter: str
    title: str
    text: str
    language: Language = Language.RUSSIAN


@dataclass
class ParserPatterns:
    """
    Regular expression patterns for document structure detection.
    
    Attributes:
        article: Pattern to match article headers.
        section: Pattern to match section headers.
        chapter: Pattern to match chapter headers.
        no_section_label: Default label when no section is found.
        no_chapter_label: Default label when no chapter is found.
    """
    
    article: Pattern[str] = field(default=None)
    section: Pattern[str] = field(default=None)
    chapter: Pattern[str] = field(default=None)
    no_section_label: str = "НЕТ РАЗДЕЛА"
    no_chapter_label: str = "НЕТ ГЛАВЫ"


class PatternFactory:
    """
    Factory class for creating language-specific parsing patterns.
    
    Provides predefined patterns for Russian and Kyrgyz legal documents.
    """
    
    @staticmethod
    def get_patterns(language: Language) -> ParserPatterns:
        """
        Get parsing patterns for the specified language.
        
        Parameters:
            language: The target language enum value.
            
        Returns:
            ParserPatterns: Configured patterns for the language.
            
        Raises:
            ValueError: If language is not supported.
        """
        if language == Language.RUSSIAN:
            return ParserPatterns(
                article=re.compile(
                    r'^\s*(Статья\s+[\d\.\-\s]+.*)',
                    re.IGNORECASE
                ),
                section=re.compile(
                    r'^\s*(РАЗДЕЛ\s+.*|Раздел\s+.*)',
                    re.IGNORECASE
                ),
                chapter=re.compile(
                    r'^\s*(ГЛАВА\s+.*|Глава\s+.*)',
                    re.IGNORECASE
                ),
                no_section_label="НЕТ РАЗДЕЛА",
                no_chapter_label="НЕТ ГЛАВЫ"
            )
        elif language == Language.KYRGYZ:
            return ParserPatterns(
                article=re.compile(
                    r'^\s*(\d+\s*-\s*(?:берене|статья).*|'
                    r'(?:берене|статья)\s+[\d\.\-\s]+.*)',
                    re.IGNORECASE
                ),
                section=re.compile(
                    r'^\s*(.*БӨЛҮМ.*)',
                    re.IGNORECASE
                ),
                chapter=re.compile(
                    r'^\s*(.*ГЛАВА.*)',
                    re.IGNORECASE
                ),
                no_section_label="БӨЛҮМ ЖОК",
                no_chapter_label="ГЛАВА ЖОК"
            )
        else:
            raise ValueError(f"Unsupported language: {language}")


class DocumentParser:
    """
    Parser for extracting structured articles from DOCX legal documents.
    
    Supports multiple languages with configurable patterns for detecting
    articles, sections, and chapters in legal documents.
    
    Attributes:
        language: The language of documents to parse.
        patterns: Regular expression patterns for structure detection.
        input_directory: Directory containing DOCX files to process.
    """
    
    OUTPUT_EXTENSION: Final[str] = ".jsonl"
    
    def __init__(
        self,
        language: Language = Language.RUSSIAN,
        input_directory: Optional[str] = None,
        custom_patterns: Optional[ParserPatterns] = None
    ) -> None:
        """
        Initialize the document parser.
        
        Parameters:
            language: Target language for parsing patterns.
            input_directory: Path to directory with DOCX files.
            custom_patterns: Custom patterns to override defaults.
        """
        self.language = language
        self.patterns = custom_patterns or PatternFactory.get_patterns(language)
        
        # Set default input directory based on language
        if input_directory is None:
            if language == Language.RUSSIAN:
                self.input_directory = "parser/docx"
            else:
                self.input_directory = f"parser/docx_{language.value}"
        else:
            self.input_directory = input_directory
    
    def parse_document(self, file_path: str) -> List[Article]:
        """
        Parse a single DOCX document into a list of articles.
        
        Reads the document and extracts articles with their metadata
        including section and chapter context.
        
        Parameters:
            file_path: Path to the DOCX file.
            
        Returns:
            List[Article]: List of parsed articles with metadata.
        """
        try:
            doc = Document(file_path)
        except Exception as e:
            print(f"   [ОШИБКА] Не удалось загрузить документ "
                  f"'{os.path.basename(file_path)}': {e}")
            return []
        
        articles: List[Article] = []
        current_article_text = ""
        current_article_title = ""
        current_section = self.patterns.no_section_label
        current_chapter = self.patterns.no_chapter_label
        article_started = False
        source_filename = os.path.basename(file_path)
        
        for paragraph in doc.paragraphs:
            # Clean text: remove extra spaces, tabs, and newlines
            text = paragraph.text.strip()
            text = re.sub(r'\s+', ' ', text).strip()
            
            if not text:
                continue
            
            match_article = self.patterns.article.match(text)
            match_section = self.patterns.section.match(text)
            match_chapter = self.patterns.chapter.match(text)
            
            if match_article:
                # Save previous article if exists
                if article_started:
                    articles.append(Article(
                        source_doc=source_filename,
                        section=current_section,
                        chapter=current_chapter,
                        title=current_article_title.strip(),
                        text=current_article_text.strip(),
                        language=self.language
                    ))
                
                # Start new article
                article_started = True
                current_article_title = text
                current_article_text = text + "\n"
                
            elif match_section:
                current_section = text
                
            elif match_chapter:
                current_chapter = text
                
            else:
                if article_started:
                    current_article_text += text + "\n"
                else:
                    # Handle continuation of chapter/section titles (for Kyrgyz)
                    if self.language == Language.KYRGYZ:
                        if current_chapter != self.patterns.no_chapter_label:
                            current_chapter += " " + text
                        elif current_section != self.patterns.no_section_label:
                            current_section += " " + text
        
        # Save last article
        if article_started:
            articles.append(Article(
                source_doc=source_filename,
                section=current_section,
                chapter=current_chapter,
                title=current_article_title.strip(),
                text=current_article_text.strip(),
                language=self.language
            ))
        
        return articles
    
    def parse_directory(
        self,
        save_jsonl: bool = True,
        output_directory: Optional[str] = None
    ) -> List[Article]:
        """
        Parse all DOCX files in the input directory.
        
        Parameters:
            save_jsonl: Whether to save results as JSONL files.
            output_directory: Directory for JSONL output files.
            
        Returns:
            List[Article]: All parsed articles from all documents.
        """
        all_articles: List[Article] = []
        processed_files = 0
        
        print(f"--- ЗАПУСК ПАРСЕРА [{self.language.name}] DOCX ---> JSONL ---")
        print(f"Ищем DOCX файлы в папке: {os.path.abspath(self.input_directory)}")
        
        if not os.path.exists(self.input_directory):
            print(f"[ОШИБКА] Папка не найдена: {self.input_directory}")
            return []
        
        for filename in os.listdir(self.input_directory):
            if filename.endswith(".docx"):
                file_path = os.path.join(self.input_directory, filename)
                print(f"\n---> ОБРАБОТКА: {filename}")
                
                articles = self.parse_document(file_path)
                
                if articles:
                    if save_jsonl:
                        output_jsonl = filename.replace(
                            ".docx",
                            self.OUTPUT_EXTENSION
                        )
                        if output_directory:
                            os.makedirs(output_directory, exist_ok=True)
                            output_path = os.path.join(
                                output_directory,
                                output_jsonl
                            )
                        else:
                            output_path = output_jsonl
                        
                        self.save_articles_to_jsonl(articles, output_path)
                        print(f"   -> Сохранено: {output_path}")
                    
                    print(f"   [ГОТОВО] Найдено {len(articles)} статей.")
                    all_articles.extend(articles)
                    processed_files += 1
        
        print("\n" + "=" * 50)
        print(f"✅ ПАРСИНГ [{self.language.name}] ЗАВЕРШЕН!")
        print(f"Обработано файлов: {processed_files}. "
              f"Всего статей: {len(all_articles)}")
        print("=" * 50)
        
        return all_articles
    
    @staticmethod
    def save_articles_to_jsonl(articles: List[Article], output_file: str) -> None:
        """
        Save articles to a JSONL (JSON Lines) file.
        
        Parameters:
            articles: List of Article objects to save.
            output_file: Path to the output JSONL file.
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            for article in articles:
                article_dict = {
                    "source_doc": article.source_doc,
                    "section": article.section,
                    "chapter": article.chapter,
                    "title": article.title,
                    "text": article.text,
                    "language": article.language.value
                }
                json_line = json.dumps(article_dict, ensure_ascii=False)
                f.write(json_line + '\n')
    
    @staticmethod
    def load_articles_from_jsonl(file_path: str) -> List[Article]:
        """
        Load articles from a JSONL file.
        
        Parameters:
            file_path: Path to the JSONL file.
            
        Returns:
            List[Article]: Loaded articles.
        """
        articles: List[Article] = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                lang_value = data.get("language", "ru")
                language = (Language.KYRGYZ if lang_value == "kg" 
                           else Language.RUSSIAN)
                articles.append(Article(
                    source_doc=data["source_doc"],
                    section=data["section"],
                    chapter=data["chapter"],
                    title=data["title"],
                    text=data["text"],
                    language=language
                ))
        return articles


# Convenience functions for backward compatibility
def parse_russian_documents(
    input_dir: str = "parser/docx",
    save_jsonl: bool = True
) -> List[Article]:
    """
    Parse Russian language documents.
    
    Parameters:
        input_dir: Directory containing DOCX files.
        save_jsonl: Whether to save JSONL output.
        
    Returns:
        List[Article]: Parsed articles.
    """
    parser = DocumentParser(Language.RUSSIAN, input_dir)
    return parser.parse_directory(save_jsonl=save_jsonl)


def parse_kyrgyz_documents(
    input_dir: str = "parser/docx_kg",
    save_jsonl: bool = True
) -> List[Article]:
    """
    Parse Kyrgyz language documents.
    
    Parameters:
        input_dir: Directory containing DOCX files.
        save_jsonl: Whether to save JSONL output.
        
    Returns:
        List[Article]: Parsed articles.
    """
    parser = DocumentParser(Language.KYRGYZ, input_dir)
    return parser.parse_directory(save_jsonl=save_jsonl)
