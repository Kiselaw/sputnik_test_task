from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.app.api import files as files_api
from src.app.api.dependencies import get_alert_service, get_file_service
from src.app.main import app
from src.core.errors import NotFoundError


NOW = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def make_file(file_id: str = "file-1", title: str = "Report") -> dict:
    return {
        "id": file_id,
        "title": title,
        "original_name": "report.txt",
        "mime_type": "text/plain",
        "size": 12,
        "processing_status": "uploaded",
        "scan_status": None,
        "scan_details": None,
        "metadata_json": None,
        "requires_attention": False,
        "created_at": NOW,
        "updated_at": NOW,
    }


def make_alert(alert_id: int = 1, file_id: str = "file-1") -> dict:
    return {
        "id": alert_id,
        "file_id": file_id,
        "level": "info",
        "message": "File processed successfully",
        "created_at": NOW,
    }


class FakeFileService:
    def __init__(self) -> None:
        self.deleted_file_ids: list[str] = []
        self.updated_titles: list[tuple[str, str]] = []

    async def list_files(self) -> list[dict]:
        return [make_file()]

    async def get_file(self, file_id: str) -> dict:
        return make_file(file_id=file_id)

    async def create_file(self, title: str, upload_file) -> SimpleNamespace:
        assert title == "Uploaded"
        assert upload_file.filename == "sample.txt"
        return SimpleNamespace(**make_file(file_id="created-file", title=title))

    async def update_file(self, file_id: str, title: str) -> dict:
        self.updated_titles.append((file_id, title))
        return make_file(file_id=file_id, title=title)

    async def delete_file(self, file_id: str) -> None:
        self.deleted_file_ids.append(file_id)

    async def get_file_download(self, file_id: str):
        return SimpleNamespace(
            mime_type="text/plain", original_name=f"{file_id}.txt"
        ), None


class FakeAlertService:
    async def list_alerts(self) -> list[dict]:
        return [make_alert()]


class NotFoundFileService(FakeFileService):
    async def get_file(self, file_id: str) -> dict:
        raise NotFoundError("File not found")


class DownloadFileService(FakeFileService):
    def __init__(self, stored_path) -> None:
        super().__init__()
        self.stored_path = stored_path

    async def get_file_download(self, file_id: str):
        file_item = SimpleNamespace(
            mime_type="text/plain", original_name=f"{file_id}.txt"
        )
        return file_item, self.stored_path


def make_client(file_service=None, alert_service=None) -> TestClient:
    app.dependency_overrides.clear()
    app.dependency_overrides[get_file_service] = lambda: (
        file_service or FakeFileService()
    )
    app.dependency_overrides[get_alert_service] = lambda: (
        alert_service or FakeAlertService()
    )
    return TestClient(app)


def test_list_files_endpoint_returns_files() -> None:
    with make_client() as client:
        response = client.get("/files/")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "file-1"
    assert response.json()[0]["title"] == "Report"


def test_get_file_endpoint_returns_file() -> None:
    with make_client() as client:
        response = client.get("/files/file-42")

    assert response.status_code == 200
    assert response.json()["id"] == "file-42"


def test_create_file_endpoint_queues_processing_task(monkeypatch) -> None:
    queued_file_ids: list[str] = []
    monkeypatch.setattr(
        files_api,
        "process_uploaded_file_task",
        SimpleNamespace(delay=queued_file_ids.append),
    )

    with make_client() as client:
        response = client.post(
            "/files/",
            data={"title": "Uploaded"},
            files={"file": ("sample.txt", b"hello", "text/plain")},
        )

    assert response.status_code == 201
    assert response.json()["id"] == "created-file"
    assert queued_file_ids == ["created-file"]


def test_update_file_endpoint_returns_updated_file() -> None:
    service = FakeFileService()

    with make_client(file_service=service) as client:
        response = client.patch("/files/file-1", json={"title": "Renamed"})

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"
    assert service.updated_titles == [("file-1", "Renamed")]


def test_delete_file_endpoint_returns_no_content() -> None:
    service = FakeFileService()

    with make_client(file_service=service) as client:
        response = client.delete("/files/file-1")

    assert response.status_code == 204
    assert response.content == b""
    assert service.deleted_file_ids == ["file-1"]


def test_download_file_endpoint_returns_file_content(tmp_path) -> None:
    stored_path = tmp_path / "file-1.txt"
    stored_path.write_text("hello", encoding="utf-8")

    with make_client(file_service=DownloadFileService(stored_path)) as client:
        response = client.get("/files/file-1/download")

    assert response.status_code == 200
    assert response.text == "hello"
    assert response.headers["content-type"].startswith("text/plain")


def test_not_found_errors_are_mapped_to_404() -> None:
    with make_client(file_service=NotFoundFileService()) as client:
        response = client.get("/files/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}


def test_list_alerts_endpoint_returns_alerts() -> None:
    with make_client() as client:
        response = client.get("/alerts/")

    assert response.status_code == 200
    assert response.json()[0]["file_id"] == "file-1"
    assert response.json()[0]["level"] == "info"
