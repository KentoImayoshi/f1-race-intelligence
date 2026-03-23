from fastapi import APIRouter

from f1_api.api.routes import explanations, health, insights, models, meta, pipeline

router = APIRouter()
router.include_router(health.router)
router.include_router(insights.router)
router.include_router(explanations.router)
router.include_router(models.router)
router.include_router(meta.router)
router.include_router(pipeline.router)
