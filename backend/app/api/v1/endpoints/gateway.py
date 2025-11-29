"""Gateway endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.schemas.gateway import ChatCompletionRequest, GatewayResponse, PIIDetectionRequest, PIIDetectionResponse
from app.services.gateway_service import GatewayService
from app.pii.detector import pii_detector

router = APIRouter()


@router.post("/chat/completions", response_model=GatewayResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Main gateway endpoint for chat completions."""
    gateway_service = GatewayService(db)
    
    try:
        response = await gateway_service.process_request(
            user_id=user.id,
            messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
            model=request.model,
            provider=request.provider,
            detection_mode=request.detection_mode or "fast",
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-pii", response_model=PIIDetectionResponse)
async def detect_pii(
    request: PIIDetectionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Standalone PII detection endpoint."""
    result = pii_detector.detect(request.text, request.mode or "fast")
    return PIIDetectionResponse(**result.to_dict())

