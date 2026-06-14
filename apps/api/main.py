from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.logging import configure_logging
from routes import agents, documents, health, reports, workflows

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="ATower Of Agents API",
    version="0.1.0",
    description="Base control-plane scaffold. Product workflows are not implemented yet.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(workflows.router)
app.include_router(documents.router)
app.include_router(agents.router)
app.include_router(reports.router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": "tower-api", "docs": "/docs", "health": "/health"}

