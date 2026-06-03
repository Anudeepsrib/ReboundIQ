from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.core import security  # PR-3: JWT + get_current_user + blacklist + owner checks (loaded for deps)

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


# Request ID middleware (observability)
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id", "dev-" + str(hash(request.url.path)))
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION, "ai": settings.AI_PROVIDER}


@app.get("/ready")
async def ready():
    # TODO: check DB, redis, ollama /api/tags
    return {"status": "ready"}


@app.get("/")
async def root():
    return {"message": "ReboundIQ API - Layoff-to-Offer Copilot", "docs": "/docs"}
