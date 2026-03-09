"""
Entry point for the Law RAG System FastAPI server.

Usage:
    python run_api.py [--host HOST] [--port PORT] [--reload]

Examples:
    python run_api.py
    python run_api.py --host 0.0.0.0 --port 8080
    python run_api.py --reload   # development mode with auto-reload
"""
import argparse
import logging

import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Law RAG System — FastAPI server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development only)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1; ignored when --reload is set)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logger.info(
        "Starting Law RAG API on http://%s:%d  (reload=%s, workers=%d)",
        args.host,
        args.port,
        args.reload,
        args.workers,
    )
    logger.info("API docs: http://%s:%d/docs", args.host, args.port)

    uvicorn.run(
        "api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=1 if args.reload else args.workers,
        log_level="info",
    )


if __name__ == "__main__":
    main()
