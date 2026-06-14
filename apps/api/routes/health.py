from fastapi import APIRouter, Depends

from core.config import Settings, get_settings
from models.schemas import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        service="tower-api",
        status="ok",
        environment=settings.app_env,
        integrations={
            "supabase": "configured" if settings.supabase_url else "unconfigured",
            "llm": settings.llm_provider,
            "band": settings.band_mode,
            "embeddings": settings.embedding_provider,
        },
    )

