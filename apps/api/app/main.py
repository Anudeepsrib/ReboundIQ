from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.core import security  # PR-3: JWT + get_current_user + blacklist + owner checks (loaded for deps)
from app.core.middleware import add_request_id  # PR-4 request id + observability for gateway/audit
from app.ai.gateway import gateway  # PR-5 / ollama default + health

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: check connections etc (ollama health in compose)
    logger = structlog.get_logger()
    logger.info(
        "app.startup",
        version=settings.VERSION,
        env=settings.ENV,
        ai_provider=settings.AI_PROVIDER,
    )
    yield
    logger.info("app.shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS (tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware (observability) - from core for PR-4 propagation to gateway/audit
app.middleware("http")(add_request_id)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION, "ai": settings.AI_PROVIDER}


@app.get("/ready")
async def ready():
    # Local ollama via gateway (uses /api/tags + model presence for local mode)
    ai = {"provider": settings.AI_PROVIDER}
    if settings.AI_PROVIDER == "ollama":
        h = await gateway.local_health()
        ai.update(h)
        ollama_ready = bool(
            h.get("local") and not h.get("error") and h.get("model_present", False)
        )
        status = "ready" if ollama_ready else "degraded"
    else:
        status = "ready"
    return {"status": status, "ai": ai}


@app.get("/")
async def root():
    return {"message": "ReboundIQ API - Layoff-to-Offer Copilot", "docs": "/docs"}
