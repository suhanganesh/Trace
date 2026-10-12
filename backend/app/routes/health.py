from fastapi import APIRouter, Response

from app.database.mongodb import ping_database
from app.schemas.responses import HealthResponse
from app.utils.config import get_settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service and database health",
)
def health_check(response: Response) -> HealthResponse:
    settings = get_settings()
    connected = ping_database()
    if not connected:
        response.status_code = 503
        return HealthResponse(
            status="degraded",
            database="disconnected",
            database_name=settings.mongodb_database,
        )
    return HealthResponse(
        status="healthy",
        database="connected",
        database_name=settings.mongodb_database,
    )
