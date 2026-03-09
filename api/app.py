"""
FastAPI application for Law RAG System.

Exposes all search modes (base, pro, search) over HTTP with
support for chat history via previous_response_id.

Endpoints:
    GET  /health           — liveness check
    POST /v1/query         — text query
    POST /v1/query/doc     — PDF document query (by URL)
    POST /v1/query/image   — image / screenshot query (by URL)
"""
import logging
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl

from searchers.search import ProLawRAGSearch

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Law RAG System API",
    description=(
        "REST API для системы поиска по законодательству Кыргызстана. "
        "Поддерживает режимы base / pro / search и управление историей "
        "диалога через previous_response_id."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Singleton searcher (lazy init on first request)
# ---------------------------------------------------------------------------
_searcher: Optional[ProLawRAGSearch] = None


def get_searcher() -> ProLawRAGSearch:
    """Return or create the singleton ProLawRAGSearch instance."""
    global _searcher
    if _searcher is None:
        _searcher = ProLawRAGSearch(top_k=3, n_llm_questions=10)
    return _searcher


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

SearchMode = Literal["base", "pro", "search"]
LangCode = Literal["ru", "kg"]


class QueryRequest(BaseModel):
    """Request body for a plain-text query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Вопрос пользователя.",
        examples=["Какие права имеет работник при увольнении?"],
    )
    type: SearchMode = Field(
        default="base",
        description=(
            "Режим поиска: "
            "**base** — прямой поиск + LLM, "
            "**pro** — LLM-генерация запросов + поиск + LLM, "
            "**search** — только векторный поиск без LLM."
        ),
    )
    lang: LangCode = Field(
        default="ru",
        description="Язык ответа: **ru** — русский, **kg** — кыргызский.",
    )
    previous_response_id: Optional[str] = Field(
        default=None,
        description=(
            "ID предыдущего ответа (из поля response_id) для продолжения "
            "диалога. Используйте для передачи истории чата."
        ),
        examples=["resp_abc123"],
    )


class DocQueryRequest(BaseModel):
    """Request body for a PDF-document query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Вопрос о документе.",
        examples=["Законен ли данный договор?"],
    )
    file_url: str = Field(
        ...,
        description="Прямая ссылка на PDF-документ.",
        examples=["https://example.com/document.pdf"],
    )
    type: Literal["base", "pro"] = Field(
        default="base",
        description="Режим анализа: **base** или **pro**.",
    )
    lang: LangCode = Field(default="ru", description="Язык ответа.")
    previous_response_id: Optional[str] = Field(
        default=None,
        description="ID предыдущего ответа для продолжения диалога.",
    )


class ImageQueryRequest(BaseModel):
    """Request body for an image (document screenshot) query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Вопрос об изображении документа.",
        examples=["Проверь соответствие этого приказа законодательству."],
    )
    image_url: str = Field(
        ...,
        description="Прямая ссылка на изображение (JPEG, PNG, GIF, WebP).",
        examples=["https://example.com/scan.jpg"],
    )
    type: Literal["base", "pro"] = Field(
        default="base",
        description="Режим анализа: **base** или **pro**.",
    )
    lang: LangCode = Field(default="ru", description="Язык ответа.")
    previous_response_id: Optional[str] = Field(
        default=None,
        description="ID предыдущего ответа для продолжения диалога.",
    )


class RAGResponse(BaseModel):
    """Unified response body for all query endpoints."""

    response: str = Field(description="Сгенерированный ответ или результаты поиска.")
    response_id: Optional[str] = Field(
        default=None,
        description=(
            "ID ответа (OpenAI Responses API). Передайте в следующем запросе "
            "как previous_response_id для продолжения диалога. "
            "Равен null в режиме search."
        ),
    )
    mode: str = Field(description="Использованный режим поиска.")
    lang: str = Field(description="Язык ответа.")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Проверка доступности сервиса",
    tags=["System"],
)
async def health() -> HealthResponse:
    """Return 200 OK when the service is running."""
    return HealthResponse(status="ok")


@app.post(
    "/v1/query",
    response_model=RAGResponse,
    summary="Текстовый запрос",
    tags=["Query"],
    status_code=status.HTTP_200_OK,
)
async def query_text(req: QueryRequest) -> RAGResponse:
    """
    Обработка текстового вопроса.

    - **base** — прямой векторный поиск + ответ LLM.
    - **pro** — LLM сначала генерирует поисковые запросы, затем ищет и отвечает.
    - **search** — возвращает найденные статьи без LLM-ответа.

    Для продолжения диалога передайте `previous_response_id` из предыдущего ответа.
    """
    logger.info("POST /v1/query type=%s lang=%s prev=%s", req.type, req.lang, req.previous_response_id)

    text, response_id = await get_searcher().get_response_text(
        query=req.query,
        type=req.type,
        lang=req.lang,
        previous_response_id=req.previous_response_id,
    )

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Не удалось получить ответ. Попробуйте переформулировать вопрос.",
        )

    return RAGResponse(response=text, response_id=response_id, mode=req.type, lang=req.lang)


@app.post(
    "/v1/query/doc",
    response_model=RAGResponse,
    summary="Анализ PDF-документа",
    tags=["Query"],
    status_code=status.HTTP_200_OK,
)
async def query_doc(req: DocQueryRequest) -> RAGResponse:
    """
    Анализ PDF-документа по прямой ссылке.

    Система извлекает текст документа, ищет релевантные нормы закона и
    генерирует юридическое заключение.

    Для продолжения диалога передайте `previous_response_id`.
    """
    logger.info("POST /v1/query/doc type=%s lang=%s prev=%s", req.type, req.lang, req.previous_response_id)

    text, response_id = await get_searcher().get_response_from_doc_text(
        query=req.query,
        file_url=req.file_url,
        type=req.type,
        lang=req.lang,
        previous_response_id=req.previous_response_id,
    )

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Не удалось обработать документ или получить ответ.",
        )

    return RAGResponse(response=text, response_id=response_id, mode=req.type, lang=req.lang)


@app.post(
    "/v1/query/image",
    response_model=RAGResponse,
    summary="Анализ изображения документа",
    tags=["Query"],
    status_code=status.HTTP_200_OK,
)
async def query_image(req: ImageQueryRequest) -> RAGResponse:
    """
    Анализ скана / скриншота документа по прямой ссылке на изображение.

    Система извлекает текст из изображения, ищет релевантные нормы закона и
    генерирует юридическое заключение.

    Для продолжения диалога передайте `previous_response_id`.
    """
    logger.info("POST /v1/query/image type=%s lang=%s prev=%s", req.type, req.lang, req.previous_response_id)

    text, response_id = await get_searcher().get_response_from_image_text(
        query=req.query,
        image_url=req.image_url,
        type=req.type,
        lang=req.lang,
        previous_response_id=req.previous_response_id,
    )

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Не удалось обработать изображение или получить ответ.",
        )

    return RAGResponse(response=text, response_id=response_id, mode=req.type, lang=req.lang)
