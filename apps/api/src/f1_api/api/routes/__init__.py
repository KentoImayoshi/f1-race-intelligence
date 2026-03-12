from fastapi import APIRouter

from f1_api.api.routes import health

router = APIRouter()
router.include_router(health.router)
