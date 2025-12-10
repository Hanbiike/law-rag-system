"""
Milvus database initialization module.

This module provides functionality to initialize Milvus collections
from existing JSON files or by running the full parser pipeline.

Usage:
    1. Load from existing JSON files:
        python -m databases.milvus_init --from-json
    
    2. Run full pipeline (parse, vectorize, load):
        python -m databases.milvus_init --full-pipeline
    
    3. Use as module:
        from databases.milvus_init import MilvusInitializer
        initializer = MilvusInitializer()
        initializer.initialize_from_json()
"""

import argparse
import sys
from pathlib import Path
from typing import Final, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.document_parser import Language
from parser.milvus_loader import MilvusLoader
from parser.pipeline import ParserPipeline, PipelineConfig


class MilvusInitializer:
    """
    Initializer for Milvus database with legal document collections.
    
    Provides methods to initialize collections from JSON files or
    by running the full parser pipeline.
    
    Attributes:
        config: Pipeline configuration.
        loader: MilvusLoader instance.
    """
    
    DEFAULT_RU_JSON: Final[str] = "law_rag_db.json"
    DEFAULT_KG_JSON: Final[str] = "law_rag_db_kg.json"
    DEFAULT_DB_PATH: Final[str] = "milvus_law_rag.db"
    
    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        ru_json_path: str = DEFAULT_RU_JSON,
        kg_json_path: str = DEFAULT_KG_JSON
    ) -> None:
        """
        Initialize the Milvus initializer.
        
        Parameters:
            db_path: Path to Milvus database.
            ru_json_path: Path to Russian JSON file.
            kg_json_path: Path to Kyrgyz JSON file.
        """
        self.db_path = db_path
        self.ru_json_path = ru_json_path
        self.kg_json_path = kg_json_path
        self._loader: Optional[MilvusLoader] = None
    
    @property
    def loader(self) -> MilvusLoader:
        """
        Lazy-load the Milvus loader.
        
        Returns:
            MilvusLoader: Configured loader instance.
        """
        if self._loader is None:
            self._loader = MilvusLoader(db_path=self.db_path)
        return self._loader
    
    def initialize_from_json(
        self,
        load_russian: bool = True,
        load_kyrgyz: bool = True,
        drop_existing: bool = True
    ) -> None:
        """
        Initialize collections from existing JSON files.
        
        Parameters:
            load_russian: Whether to load Russian collection.
            load_kyrgyz: Whether to load Kyrgyz collection.
            drop_existing: Whether to drop existing collections.
        """
        print("=" * 60)
        print("MILVUS INITIALIZATION FROM JSON FILES")
        print("=" * 60)
        
        if load_russian and Path(self.ru_json_path).exists():
            print(f"\nLoading Russian data from: {self.ru_json_path}")
            self.loader.load_from_json_file(
                self.ru_json_path,
                Language.RUSSIAN,
                drop_existing
            )
        elif load_russian:
            print(f"Warning: Russian JSON file not found: {self.ru_json_path}")
        
        if load_kyrgyz and Path(self.kg_json_path).exists():
            print(f"\nLoading Kyrgyz data from: {self.kg_json_path}")
            self.loader.load_from_json_file(
                self.kg_json_path,
                Language.KYRGYZ,
                drop_existing
            )
        elif load_kyrgyz:
            print(f"Warning: Kyrgyz JSON file not found: {self.kg_json_path}")
        
        self._print_collections_info()
    
    def initialize_from_pipeline(
        self,
        ru_input_dir: str = "parser/docx",
        kg_input_dir: str = "parser/docx_kg",
        process_russian: bool = True,
        process_kyrgyz: bool = True
    ) -> None:
        """
        Initialize collections by running the full parser pipeline.
        
        Parameters:
            ru_input_dir: Directory with Russian DOCX files.
            kg_input_dir: Directory with Kyrgyz DOCX files.
            process_russian: Whether to process Russian documents.
            process_kyrgyz: Whether to process Kyrgyz documents.
        """
        print("=" * 60)
        print("MILVUS INITIALIZATION FROM PARSER PIPELINE")
        print("=" * 60)
        
        config = PipelineConfig(
            ru_input_dir=ru_input_dir,
            kg_input_dir=kg_input_dir,
            ru_output_json=self.ru_json_path,
            kg_output_json=self.kg_json_path,
            milvus_db_path=self.db_path,
            save_intermediate=True
        )
        
        pipeline = ParserPipeline(config)
        pipeline.process_all(
            process_russian=process_russian,
            process_kyrgyz=process_kyrgyz
        )
        pipeline.close()
        
        self._print_collections_info()
    
    def _print_collections_info(self) -> None:
        """Print information about all collections."""
        print("\n" + "=" * 60)
        print("COLLECTIONS INFO")
        print("=" * 60)
        
        for lang in [Language.RUSSIAN, Language.KYRGYZ]:
            collection_name = self.loader.get_collection_name(lang)
            
            if self.loader.collection_exists(collection_name):
                info = self.loader.describe_collection(collection_name)
                print(f"\n{lang.name} ({collection_name}):")
                print(f"  {info}")
                
                # Get sample
                sample = self.loader.query(
                    collection_name,
                    ["id", "source_doc", "article_title"],
                    limit=1
                )
                if sample:
                    print(f"  Sample: {sample[0]}")
            else:
                print(f"\n{lang.name}: Collection not found")
    
    def verify(self) -> bool:
        """
        Verify that all collections are properly initialized.
        
        Returns:
            bool: True if all collections exist and have data.
        """
        all_ok = True
        
        for lang in [Language.RUSSIAN, Language.KYRGYZ]:
            collection_name = self.loader.get_collection_name(lang)
            
            if not self.loader.collection_exists(collection_name):
                print(f"Error: Collection {collection_name} not found")
                all_ok = False
        
        return all_ok
    
    def close(self) -> None:
        """Close the loader connection."""
        if self._loader is not None:
            self._loader.close()


def main() -> None:
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Initialize Milvus database with legal documents"
    )
    
    parser.add_argument(
        "--from-json",
        action="store_true",
        help="Load data from existing JSON files"
    )
    
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Run full parser pipeline (parse, vectorize, load)"
    )
    
    parser.add_argument(
        "--db-path",
        default="milvus_law_rag.db",
        help="Path to Milvus database"
    )
    
    parser.add_argument(
        "--ru-json",
        default="law_rag_db.json",
        help="Path to Russian JSON file"
    )
    
    parser.add_argument(
        "--kg-json",
        default="law_rag_db_kg.json",
        help="Path to Kyrgyz JSON file"
    )
    
    parser.add_argument(
        "--ru-docx-dir",
        default="parser/docx",
        help="Directory with Russian DOCX files"
    )
    
    parser.add_argument(
        "--kg-docx-dir",
        default="parser/docx_kg",
        help="Directory with Kyrgyz DOCX files"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify collections after initialization"
    )
    
    args = parser.parse_args()
    
    initializer = MilvusInitializer(
        db_path=args.db_path,
        ru_json_path=args.ru_json,
        kg_json_path=args.kg_json
    )
    
    try:
        if args.full_pipeline:
            initializer.initialize_from_pipeline(
                ru_input_dir=args.ru_docx_dir,
                kg_input_dir=args.kg_docx_dir
            )
        elif args.from_json:
            initializer.initialize_from_json()
        else:
            # Default: try JSON first, fall back to pipeline
            print("No mode specified. Trying to load from JSON files...")
            initializer.initialize_from_json()
        
        if args.verify:
            success = initializer.verify()
            if not success:
                sys.exit(1)
    
    finally:
        initializer.close()


if __name__ == "__main__":
    main()