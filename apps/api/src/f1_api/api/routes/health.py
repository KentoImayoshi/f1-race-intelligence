from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root() -> dict:
    return {"service": "f1-api"}


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
