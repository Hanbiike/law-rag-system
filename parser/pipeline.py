"""
Pipeline module for end-to-end document processing.

This module provides a unified pipeline for parsing, vectorizing,
and loading legal documents into Milvus database.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Final, List, Optional, Tuple

from parser.document_parser import Article, DocumentParser, Language
from parser.milvus_loader import MilvusLoader
from parser.vectorizer import VectorizedArticle, Vectorizer


@dataclass
class PipelineConfig:
    """
    Configuration for the parser pipeline.
    
    Attributes:
        ru_input_dir: Directory with Russian DOCX files.
        kg_input_dir: Directory with Kyrgyz DOCX files.
        ru_output_json: Output JSON file for Russian articles.
        kg_output_json: Output JSON file for Kyrgyz articles.
        milvus_db_path: Path to Milvus database.
        model_name: SentenceTransformer model name.
        embedding_dimension: Vector embedding dimension.
        save_intermediate: Whether to save intermediate JSON files.
    """
    
    ru_input_dir: str = "parser/docx"
    kg_input_dir: str = "parser/docx_kg"
    ru_output_json: str = "law_rag_db.json"
    kg_output_json: str = "law_rag_db_kg.json"
    milvus_db_path: str = "milvus_law_rag.db"
    model_name: str = "google/embeddinggemma-300m"
    embedding_dimension: int = 768
    save_intermediate: bool = True


class ParserPipeline:
    """
    End-to-end pipeline for document processing.
    
    Combines parsing, vectorization, and database loading into
    a single, easy-to-use interface.
    
    Attributes:
        config: Pipeline configuration.
        vectorizer: Vectorizer instance (lazy loaded).
        milvus_loader: MilvusLoader instance (lazy loaded).
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        """
        Initialize the pipeline with configuration.
        
        Parameters:
            config: Pipeline configuration. Uses defaults if None.
        """
        self.config = config or PipelineConfig()
        self._vectorizer: Optional[Vectorizer] = None
        self._milvus_loader: Optional[MilvusLoader] = None
    
    @property
    def vectorizer(self) -> Vectorizer:
        """
        Lazy-load the vectorizer.
        
        Returns:
            Vectorizer: Configured vectorizer instance.
        """
        if self._vectorizer is None:
            self._vectorizer = Vectorizer(model_name=self.config.model_name)
        return self._vectorizer
    
    @property
    def milvus_loader(self) -> MilvusLoader:
        """
        Lazy-load the Milvus loader.
        
        Returns:
            MilvusLoader: Configured loader instance.
        """
        if self._milvus_loader is None:
            self._milvus_loader = MilvusLoader(
                db_path=self.config.milvus_db_path,
                dimension=self.config.embedding_dimension
            )
        return self._milvus_loader
    
    def parse_documents(
        self,
        language: Language,
        input_dir: Optional[str] = None,
        save_jsonl: bool = False
    ) -> List[Article]:
        """
        Parse documents for a specific language.
        
        Parameters:
            language: Target language.
            input_dir: Input directory (uses config default if None).
            save_jsonl: Whether to save JSONL files.
            
        Returns:
            List[Article]: Parsed articles.
        """
        if input_dir is None:
            if language == Language.RUSSIAN:
                input_dir = self.config.ru_input_dir
            else:
                input_dir = self.config.kg_input_dir
        
        parser = DocumentParser(language=language, input_directory=input_dir)
        return parser.parse_directory(save_jsonl=save_jsonl)
    
    def vectorize_articles(
        self,
        articles: List[Article],
        start_id: int = 1
    ) -> List[VectorizedArticle]:
        """
        Vectorize a list of articles.
        
        Parameters:
            articles: Articles to vectorize.
            start_id: Starting ID for articles.
            
        Returns:
            List[VectorizedArticle]: Vectorized articles.
        """
        return self.vectorizer.vectorize_articles(articles, start_id=start_id)
    
    def save_vectorized(
        self,
        articles: List[VectorizedArticle],
        output_path: str
    ) -> None:
        """
        Save vectorized articles to JSON.
        
        Parameters:
            articles: Vectorized articles to save.
            output_path: Output file path.
        """
        self.vectorizer.save_to_json(articles, output_path)
    
    def load_to_milvus(
        self,
        articles: List[VectorizedArticle],
        language: Language,
        drop_existing: bool = True
    ) -> None:
        """
        Load vectorized articles into Milvus.
        
        Parameters:
            articles: Vectorized articles to load.
            language: Target language.
            drop_existing: Whether to drop existing collection.
        """
        self.milvus_loader.setup_language_collection(
            language=language,
            articles=articles,
            drop_existing=drop_existing
        )
    
    def process_language(
        self,
        language: Language,
        input_dir: Optional[str] = None,
        output_json: Optional[str] = None,
        drop_existing: bool = True
    ) -> Tuple[List[Article], List[VectorizedArticle]]:
        """
        Process all documents for a language end-to-end.
        
        Parameters:
            language: Target language.
            input_dir: Input directory override.
            output_json: Output JSON path override.
            drop_existing: Whether to drop existing Milvus collection.
            
        Returns:
            Tuple of (parsed articles, vectorized articles).
        """
        print(f"\n{'='*60}")
        print(f"Processing {language.name} documents")
        print(f"{'='*60}\n")
        
        # 1. Parse documents
        articles = self.parse_documents(language, input_dir)
        
        if not articles:
            print(f"No articles found for {language.name}")
            return [], []
        
        # 2. Vectorize
        vectorized = self.vectorize_articles(articles)
        
        # 3. Save to JSON if configured
        if self.config.save_intermediate:
            if output_json is None:
                if language == Language.RUSSIAN:
                    output_json = self.config.ru_output_json
                else:
                    output_json = self.config.kg_output_json
            
            self.save_vectorized(vectorized, output_json)
        
        # 4. Load to Milvus
        self.load_to_milvus(vectorized, language, drop_existing)
        
        return articles, vectorized
    
    def process_all(
        self,
        process_russian: bool = True,
        process_kyrgyz: bool = True,
        drop_existing: bool = True
    ) -> Dict[Language, Tuple[List[Article], List[VectorizedArticle]]]:
        """
        Process all configured languages.
        
        Parameters:
            process_russian: Whether to process Russian documents.
            process_kyrgyz: Whether to process Kyrgyz documents.
            drop_existing: Whether to drop existing Milvus collections.
            
        Returns:
            Dict mapping language to (articles, vectorized_articles).
        """
        results: Dict[Language, Tuple] = {}
        
        if process_russian:
            results[Language.RUSSIAN] = self.process_language(
                Language.RUSSIAN,
                drop_existing=drop_existing
            )
        
        if process_kyrgyz:
            results[Language.KYRGYZ] = self.process_language(
                Language.KYRGYZ,
                drop_existing=drop_existing
            )
        
        print("\n" + "=" * 60)
        print("✅ PIPELINE COMPLETE!")
        print("=" * 60)
        
        for lang, (articles, vectorized) in results.items():
            print(f"  {lang.name}: {len(articles)} articles, "
                  f"{len(vectorized)} vectorized")
        
        return results
    
    def load_from_existing_json(
        self,
        ru_json_path: Optional[str] = None,
        kg_json_path: Optional[str] = None,
        drop_existing: bool = True
    ) -> None:
        """
        Load existing JSON files directly into Milvus.
        
        Useful when you already have vectorized JSON files and
        just need to reload them into the database.
        
        Parameters:
            ru_json_path: Path to Russian JSON file.
            kg_json_path: Path to Kyrgyz JSON file.
            drop_existing: Whether to drop existing collections.
        """
        if ru_json_path:
            print(f"\nLoading Russian articles from: {ru_json_path}")
            self.milvus_loader.load_from_json_file(
                ru_json_path,
                Language.RUSSIAN,
                drop_existing
            )
        
        if kg_json_path:
            print(f"\nLoading Kyrgyz articles from: {kg_json_path}")
            self.milvus_loader.load_from_json_file(
                kg_json_path,
                Language.KYRGYZ,
                drop_existing
            )
        
        print("\n✅ All data loaded into Milvus!")
    
    def verify_collections(self) -> None:
        """
        Verify that all collections are properly set up.
        
        Prints collection information and sample records.
        """
        print("\n" + "=" * 60)
        print("COLLECTION VERIFICATION")
        print("=" * 60)
        
        for lang in [Language.RUSSIAN, Language.KYRGYZ]:
            collection_name = self.milvus_loader.get_collection_name(lang)
            
            if self.milvus_loader.collection_exists(collection_name):
                info = self.milvus_loader.describe_collection(collection_name)
                print(f"\n{lang.name} collection ({collection_name}):")
                print(f"  Info: {info}")
                
                # Get sample record
                sample = self.milvus_loader.query(
                    collection_name,
                    output_fields=["id", "source_doc", "article_title"],
                    limit=1
                )
                if sample:
                    print(f"  Sample: {sample[0]}")
            else:
                print(f"\n{lang.name} collection does not exist")
    
    def close(self) -> None:
        """Close all connections."""
        if self._milvus_loader is not None:
            self._milvus_loader.close()


# Convenience function for quick setup
def run_full_pipeline(
    ru_input_dir: str = "parser/docx",
    kg_input_dir: str = "parser/docx_kg",
    milvus_db_path: str = "milvus_law_rag.db"
) -> None:
    """
    Run the complete pipeline with default settings.
    
    Parameters:
        ru_input_dir: Directory with Russian DOCX files.
        kg_input_dir: Directory with Kyrgyz DOCX files.
        milvus_db_path: Path to Milvus database.
    """
    config = PipelineConfig(
        ru_input_dir=ru_input_dir,
        kg_input_dir=kg_input_dir,
        milvus_db_path=milvus_db_path
    )
    
    pipeline = ParserPipeline(config)
    pipeline.process_all()
    pipeline.verify_collections()
    pipeline.close()


if __name__ == "__main__":
    run_full_pipeline()
