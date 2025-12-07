# Law RAG System

A modular Retrieval-Augmented Generation (RAG) system for legal document search and question answering, using Azure OpenAI, Milvus vector database, and custom embedding/LLM tools.

## Features
- **Semantic search** over legal documents using vector embeddings
- **LLM-powered query expansion** for better search results
- **Integration with Azure OpenAI** (multiple deployments supported)
- **Milvus vector database** for scalable similarity search
- **Modular codebase** for easy extension and adaptation

## Project Structure

```
├── aitools/
│   ├── embedder.py         # Embedding utilities
│   ├── llm.py              # LLM interaction utilities
│   └── __pycache__/
├── databases/
│   ├── db.py               # Base DB logic
│   ├── milvus_db.py        # Milvus DB integration
│   ├── milvus_migrate.py   # Migration scripts
│   ├── milvus_migrate_v2.py
│   └── __pycache__/
├── config.py               # Loads config from .env
├── pro_search.py           # Main search script (classic)
├── pro_search_milvus.py    # Main search script (Milvus)
├── search.py               # Search logic
├── law_rag_db.json         # Example DB (JSON)
├── law_rag_db_kg.json      # Example DB (KG JSON)
├── .gitignore
└── ...
```

## Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd law-rag-system
```

### 2. Create and configure `.env`
Create a `.env` file in the root directory with the following variables:

```
AZURE_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_DEPLOYMENT=your_azure_deployment
AZURE_API_VERSION=2025-03-01-preview
AZURE_ENDPOINT_NANO=your_azure_endpoint_nano
AZURE_OPENAI_API_KEY_NANO=your_azure_openai_api_key_nano
AZURE_DEPLOYMENT_NANO=your_azure_deployment_nano
AZURE_API_VERSION_NANO=2025-03-01-preview
```

### 3. Install dependencies
It is recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If `requirements.txt` is missing, install manually:
- `python-dotenv`
- `pymilvus`
- `openai` (or `azure-openai`)
- Any other dependencies used in your code

### 4. Prepare the database
- Place your legal documents in `law_rag_db.json` or `law_rag_db_kg.json`.
- Run migration scripts in `databases/` if needed to populate Milvus.

### 5. Run the system
For Milvus-based search:
```bash
python pro_search_milvus.py
```
For classic search:
```bash
python pro_search.py
```

## Usage
- Enter your query when prompted.
- The system will expand your query using LLM, search for relevant laws, and return the most similar results.
- Optionally, the LLM will generate a final answer based on the retrieved documents.

## Notes
- All secrets and API keys must be stored in `.env` (never commit them to git).
- The `.gitignore` is set up to exclude cache, DB, and secret files.
- For production, review and secure all credentials.

## License
Specify your license here.

## Authors
- Your Name (your.email@example.com)
- Contributors welcome!
