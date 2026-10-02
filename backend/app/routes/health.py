from fastapi import APIRouter

from app.schemas import HealthOut

router = APIRouter()


@router.get(
    "/health", response_model=HealthOut, tags=["health"],
    summary="Check application health",
    description="Returns ok when the application is responding. Does not call the LLM.",
)
def health_check():
    return {"status": "ok"}
