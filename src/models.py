"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel
from typing import List, Tuple, Optional, Dict, Any


class MarkerData(BaseModel):
    """Model for marker coordinates"""
    x: int
    y: int


class MarkerDetailGenerationRequest(BaseModel):
    """Request model for generating a marker-focused detail image"""
    marker_index: int
    x: Optional[int] = None
    y: Optional[int] = None


class UploadResponse(BaseModel):
    """Response model for image upload"""
    session_id: str
    width: int
    height: int
    filename: str


class MarkerResponse(BaseModel):
    """Response model for marker operations"""
    success: bool = True
    marker_count: int = 0
    markers: List[Tuple[int, int]] = []
    message: str = ""


class SessionResponse(BaseModel):
    """Response model for session operations"""
    success: bool = True
    message: str = ""


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str
    detail: str = ""


class GeneratedImageResponse(BaseModel):
    """Response model for generated image metadata"""
    id: int
    order_index: int
    prompt: str
    model: str
    created_at: str


class ImageListResponse(BaseModel):
    """Response model for paginated image list"""
    session_id: str
    page: int
    page_size: int
    total_count: int
    total_pages: int
    images: List[GeneratedImageResponse] = []


class DrillResponse(BaseModel):
    """Response model for drill operations"""
    success: bool = True
    drill_id: Optional[int] = None
    drill_name: str = ""
    seed: int = 0
    num_images: int = 0
    message: str = ""


class AnalysisResponse(BaseModel):
    """Response model for vision analysis"""
    id: int
    image_id: int
    model: str
    results: str
    confidence: Optional[float] = None
    created_at: str = ""


class SessionHistoryResponse(BaseModel):
    """Response model for session history"""
    session_id: str
    current_image_index: int = 0
    total_images: int = 0
    drill_mode: bool = False
    drill_seed: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""
