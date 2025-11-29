"""Common schemas."""

from pydantic import BaseModel
from typing import Optional, Any, Dict


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response schema."""

    success: bool = True
    message: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel):
    """Paginated response."""

    items: list[Any]
    total: int
    page: int
    page_size: int
    pages: int

