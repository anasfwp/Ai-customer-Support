import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api.v1 import auth, documents, chat, feedback, analytics
from app.core.limiter import limiter
from app.db.base import Base, engine

logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Customer Support Knowledge Assistant")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Generous ceiling for any request body (uploads have their own tighter,
# configurable limit enforced in the documents router; this just stops an
# oversized request from being parsed into memory at all).
MAX_REQUEST_BODY_BYTES = (settings.MAX_UPLOAD_SIZE_MB + 5) * 1024 * 1024


@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length is not None and content_length.isdigit():
        if int(content_length) > MAX_REQUEST_BODY_BYTES:
            return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Baseline hardening headers (defense in depth; TLS itself is
    terminated by Render's edge, not this app)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Never leak internal exception details (stack traces, library
    error text, file paths, etc.) to API clients - log them server-side
    instead and return a generic message.

    Handlers registered for the bare `Exception` class run inside
    Starlette's ServerErrorMiddleware, which wraps *outside*
    CORSMiddleware - so this response would otherwise skip CORS
    entirely and the browser would report a confusing "blocked by CORS
    policy" error that has nothing to do with CORS. Add the same header
    CORSMiddleware would have added, by hand.
    """
    logger.error("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc)
    response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
    origin = request.headers.get("origin")
    if origin and origin in settings.allowed_origins_list:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.on_event("startup")
async def on_startup():
    """Create tables (and the pgvector extension, if on Postgres) if they
    don't already exist. This project has no Alembic migrations yet, so
    this keeps a fresh deploy (e.g. on Render) usable out of the box.

    The pgvector extension and the `chunks` table (the only one that
    depends on it) are created in their own try/except, deliberately
    separate from the rest of the schema. Postgres aborts an entire
    transaction on the first failing statement, so if the extension
    isn't permitted on a given plan and this were all one block, *no*
    tables would get created - including unrelated ones like `users` and
    `tenants` - taking down the whole app instead of just RAG search.
    """
    from sqlalchemy import text
    from app.db.models import tenant, user, document, chunk, chat_log, feedback  # noqa: F401

    vector_ready = True
    if engine.dialect.name == "postgresql":
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
        except Exception:
            vector_ready = False
            logger.exception(
                "Could not create the pgvector extension - check that your Postgres "
                "plan permits CREATE EXTENSION. Continuing without it; document "
                "upload/chat will not work until this is resolved."
            )

    core_tables = [t for name, t in Base.metadata.tables.items() if name != "chunks"]
    try:
        Base.metadata.create_all(bind=engine, tables=core_tables)
        logger.info("Core database tables verified/created successfully")
    except Exception:
        logger.exception("Core database table creation failed on startup")
        return

    if vector_ready:
        try:
            Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables["chunks"]])
            logger.info("chunks table (pgvector) verified/created successfully")
        except Exception:
            logger.exception("chunks table creation failed on startup")


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


@app.get("/")
async def root():
    return {"message": "AI Customer Support Knowledge Assistant API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
