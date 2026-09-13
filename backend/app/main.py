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
    allow_origins=settings.ALLOWED_ORIGINS,
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
    instead and return a generic message."""
    logger.error("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
async def on_startup():
    """Create tables (and the pgvector extension, if on Postgres) if they
    don't already exist. This project has no Alembic migrations yet, so
    this keeps a fresh deploy (e.g. on Render) usable out of the box."""
    try:
        if engine.dialect.name == "postgresql":
            with engine.connect() as conn:
                from sqlalchemy import text

                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()

        # Import models so they're registered on Base.metadata before create_all
        from app.db.models import tenant, user, document, chunk, chat_log, feedback  # noqa: F401

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully")
    except Exception:
        logger.exception("Database initialization failed on startup")


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
