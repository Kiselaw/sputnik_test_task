from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status

import src.core.celery  # noqa: F401
from src.app.api import alerts, files
from src.app.files.storage import FileStorage
from src.core.config import settings
from src.core.errors import NotFoundError, StorageError, ValidationError


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI()
    app.state.file_storage = FileStorage(settings.storage_dir)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(files.router)
    app.include_router(alerts.router)

    return app


app = create_app()


@app.get("/health", include_in_schema=False)
async def health_check() -> dict[str, str]:
    """Return a lightweight health response."""
    return {"status": "ok"}


@app.exception_handler(NotFoundError)
async def handle_not_found_error(request: Request, exc: NotFoundError) -> JSONResponse:
    """Map domain not-found errors to HTTP 404 responses."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.message}
    )


@app.exception_handler(ValidationError)
async def handle_validation_error(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Map domain validation errors to HTTP 400 responses."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.message}
    )


@app.exception_handler(StorageError)
async def handle_storage_error(request: Request, exc: StorageError) -> JSONResponse:
    """Map storage errors to HTTP 500 responses."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.message},
    )
