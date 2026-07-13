from fastapi import APIRouter, Depends

from src.app.alerts.service import AlertService
from src.app.alerts.schemas import AlertItem
from src.app.api.dependencies import get_alert_service


router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertItem])
async def list_alerts_view(service: AlertService = Depends(get_alert_service)):
    """Return all generated file alerts."""
    return await service.list_alerts()
