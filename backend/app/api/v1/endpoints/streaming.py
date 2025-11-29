"""Streaming endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.schemas.streaming import StreamingRequest
from app.services.streaming_service import StreamingService

router = APIRouter()


@router.post("/chat/completions/stream")
async def stream_completions(
    request: StreamingRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Streaming chat completions endpoint."""
    streaming_service = StreamingService(db)
    
    async def generate():
        async for chunk in streaming_service.stream_completion(
            user_id=user.id,
            messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
            model=request.model,
            provider=request.provider,
            detection_mode=request.detection_mode or "fast",
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        ):
            yield chunk

    return StreamingResponse(generate(), media_type="text/event-stream")

