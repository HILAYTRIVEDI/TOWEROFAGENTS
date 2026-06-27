import logging

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import get_settings
from core.logging import configure_logging
from routes import agents, documents, health, reports, workflows

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ATower Of Agents API",
    version="0.1.0",
    description="Base control-plane scaffold. Product workflows are not implemented yet.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(httpx.HTTPError)
async def external_http_error_handler(request: Request, exc: httpx.HTTPError) -> JSONResponse:
    logger.warning(
        "External HTTP dependency failed for %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "External service unavailable. Check configured service URLs "
                "and network/DNS connectivity."
            )
        },
    )


app.include_router(health.router)
app.include_router(workflows.router)
app.include_router(documents.router)
app.include_router(agents.router)
app.include_router(reports.router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": "tower-api", "docs": "/docs", "health": "/health"}
