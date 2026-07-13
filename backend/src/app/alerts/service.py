from src.app.alerts.repository import AlertRepository
from src.db.models import Alert


class AlertService:
    """Coordinate alert use cases."""

    def __init__(self, alerts_repo: AlertRepository) -> None:
        """Store the request-scoped alert repository."""
        self.alerts_repo = alerts_repo

    async def list_alerts(self) -> list[Alert]:
        """Return all alerts."""
        return await self.alerts_repo.list()
