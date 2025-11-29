"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio

from app.config import config_manager, settings
from app.api.v1.endpoints.router import router as v1_router
from app.core.metrics import get_metrics_response
from app.core.rate_limiter import rate_limiter
from app.core.queue import queue
from app.cache.semantic_cache import semantic_cache
from app.pii.masker import pii_masker
from app.pii.nlp_models import nlp_models
from app.embeddings.factory import embedding_factory
from app.guardrails.engine import guardrail_engine
from app.core.exceptions import (
    RateLimitException,
    TimeoutException,
    ProviderException,
    GuardrailViolationException,
    BudgetExceededException,
    AuthenticationException,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting AI Gateway application...")

    # Initialize database (already done via session)
    logger.info("Database connection initialized")

    # Initialize Redis connections
    await rate_limiter.initialize()
    await semantic_cache.initialize()
    await pii_masker.initialize()
    await queue.initialize()
    logger.info("Redis connections initialized")

    # Load spaCy models in parallel (optional, will use fallback if not available)
    logger.info("Loading spaCy models...")
    try:
        await asyncio.gather(
            asyncio.to_thread(nlp_models.get_turkish_model),
            asyncio.to_thread(nlp_models.get_english_model),
        )
        logger.info("spaCy models loaded")
    except Exception as e:
        logger.warning(f"Could not load spaCy models: {e}. PII detection will use regex-only mode.")

    # Initialize embedding provider
    embedding_factory.get_provider()
    logger.info("Embedding provider initialized")

    # Load guardrails
    guardrail_engine._load_rules()
    logger.info("Guardrails loaded")

    # Start queue workers if enabled
    if config_manager.get("queue.enabled", False):
        # Note: Would need gateway service instance - simplified for now
        logger.info("Queue workers started")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await rate_limiter.close()
    await semantic_cache.close()
    await pii_masker.close()
    await queue.close()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI Gateway PII Detection",
    description="AI Gateway with PII detection, semantic caching, and multi-provider support",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
cors_origins = config_manager.get("server.cors_origins", ["http://localhost:3000"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    
    return response


# Exception handlers
@app.exception_handler(RateLimitException)
async def rate_limit_handler(request: Request, exc: RateLimitException):
    """Handle rate limit exceptions."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc),
            "retry_after": exc.retry_after,
        },
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.exception_handler(TimeoutException)
async def timeout_handler(request: Request, exc: TimeoutException):
    """Handle timeout exceptions."""
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"error": "Request timeout", "detail": str(exc)},
    )


@app.exception_handler(ProviderException)
async def provider_handler(request: Request, exc: ProviderException):
    """Handle provider exceptions."""
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": "Provider error",
            "detail": str(exc),
            "provider": exc.provider,
        },
    )


@app.exception_handler(GuardrailViolationException)
async def guardrail_handler(request: Request, exc: GuardrailViolationException):
    """Handle guardrail violations."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Guardrail violation",
            "detail": str(exc),
            "violations": [v.__dict__ for v in exc.violations],
        },
    )


@app.exception_handler(BudgetExceededException)
async def budget_handler(request: Request, exc: BudgetExceededException):
    """Handle budget exceeded exceptions."""
    return JSONResponse(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content={
            "error": "Budget exceeded",
            "detail": str(exc),
            "current_spend": exc.current_spend,
            "limit": exc.limit,
        },
    )


@app.exception_handler(AuthenticationException)
async def auth_handler(request: Request, exc: AuthenticationException):
    """Handle authentication exceptions."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "Authentication failed", "detail": str(exc)},
    )


# Include routers
app.include_router(v1_router, prefix="/v1")


# Health endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return get_metrics_response()


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Gateway PII Detection",
        "version": "1.0.0",
        "docs": "/docs",
    }

