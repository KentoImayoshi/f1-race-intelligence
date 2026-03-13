from fastapi import APIRouter

from f1_api.api.routes import health, insights

router = APIRouter()
router.include_router(health.router)
router.include_router(insights.router)
