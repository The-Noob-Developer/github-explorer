"""GET /api/health -- liveness/readiness probe.

Checks that settings can be loaded (i.e. the process is configured), not
that Groq or GitHub are reachable -- an external outage shouldn't make an
orchestrator think this instance is unhealthy and restart it.
"""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_app_settings
from app.config.settings import Settings
from app.models.search_models import HealthResponseModel

router = APIRouter()


@router.get("/api/health", response_model=HealthResponseModel)
async def health(settings: Settings = Depends(get_app_settings)) -> HealthResponseModel:
    # Accessing an attribute confirms settings loaded without raising.
    _ = settings.max_results
    return HealthResponseModel(status="ok")
