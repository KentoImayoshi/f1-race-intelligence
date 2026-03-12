from fastapi import FastAPI

from f1_api.api.routes import router as api_router
from f1_core.config import settings
from f1_core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
    )

    app.include_router(api_router)

    return app


app = create_app()
