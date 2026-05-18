"""
Enhanced API route handlers for Red Marker application with AI features
"""

import os
import uuid
import asyncio
import json
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse

from src.models import MarkerData, MarkerDetailGenerationRequest, UploadResponse, MarkerResponse, SessionResponse
from src.config import TEMP_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from src.utils import (
    allowed_file, validate_image, draw_markers_on_image, create_marker_detail_image,
    crop_marker_region_image, cleanup_session_files
)
from src.database import get_db, SessionLocal, GeneratedImage, SessionHistory, SavedDrill, MarkerAnnotation, init_db
from src.model_loader import get_model_manager
from src.services import ImageGenerationService, DeterministicDrill
from src.vision_service import VisionAnalysisService

logger = logging.getLogger(__name__)

# Initialize database on startup
init_db()

router = APIRouter(prefix="/api", tags=["api"])

# Global session storage (in-memory)
sessions = {}
generation_tasks = {}  # Track generation tasks

# Initialize model manager
model_manager = get_model_manager()


def get_or_recover_session(session_id: str) -> Optional[dict]:
    """Return an in-memory session or recover its uploaded file after a server restart."""
    if session_id in sessions:
        hydrate_session_markers(session_id, sessions[session_id])
        return sessions[session_id]

    matches = sorted(TEMP_DIR.glob(f"{session_id}_original_*"))
    if not matches:
        return None

    image_path = matches[0]
    try:
        with open(image_path, "rb") as image_file:
            width, height = validate_image(image_file.read())
    except Exception as e:
        logger.warning(f"Could not recover session {session_id}: {e}")
        return None

    filename = image_path.name.split("_original_", 1)[1]
    sessions[session_id] = {
        'original_path': str(image_path),
        'original_filename': filename,
        'width': width,
        'height': height,
        'markers': []
    }
    hydrate_session_markers(session_id, sessions[session_id])
    return sessions[session_id]


def hydrate_session_markers(session_id: str, session: dict) -> None:
    """Load persisted marker coordinates into a session when memory is stale."""
    if session.get('markers'):
        return

    db = SessionLocal()
    try:
        rows = db.query(MarkerAnnotation).filter(
            MarkerAnnotation.session_id == session_id
        ).order_by(MarkerAnnotation.created_at, MarkerAnnotation.id).all()
        session['markers'] = [(row.x, row.y) for row in rows]
    finally:
        db.close()


def persist_marker(session_id: str, x: int, y: int) -> None:
    db = SessionLocal()
    try:
        db.add(MarkerAnnotation(session_id=session_id, x=x, y=y))
        db.commit()
    finally:
        db.close()


def replace_persisted_markers(session_id: str, markers: list[tuple[int, int]]) -> None:
    db = SessionLocal()
    try:
        db.query(MarkerAnnotation).filter(
            MarkerAnnotation.session_id == session_id
        ).delete()
        for x, y in markers:
            db.add(MarkerAnnotation(session_id=session_id, x=x, y=y))
        db.commit()
    finally:
        db.close()


def normalize_prompts(prompts: List[str]) -> List[str]:
    """Accept repeated query params or the frontend's pipe-delimited value."""
    normalized = []
    for prompt in prompts:
        normalized.extend(part.strip() for part in prompt.split("|||"))
    return [prompt for prompt in normalized if prompt]


async def run_generation_task(
    session_id: str,
    prompts: List[str],
    interval: float,
    max_images: Optional[int],
):
    """Run generation with its own DB session so it survives the request lifecycle."""
    db = SessionLocal()
    try:
        gen_service = ImageGenerationService(db, model_manager)
        await gen_service.start_generation_loop(
            session_id=session_id,
            prompts=prompts,
            interval=interval,
            max_images=max_images,
        )
    except asyncio.CancelledError:
        raise
    finally:
        generation_tasks.pop(session_id, None)
        db.close()


# ============================================================================
# Original Endpoints (Image Upload & Marking)
# ============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """Handle image upload and initialization."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {MAX_FILE_SIZE / (1024*1024):.0f}MB limit"
            )
        
        # Validate image
        width, height = validate_image(content)
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded image temporarily
        filename = file.filename
        temp_path = os.path.join(str(TEMP_DIR), f'{session_id}_original_{filename}')
        
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Store session info
        sessions[session_id] = {
            'original_path': temp_path,
            'original_filename': filename,
            'width': width,
            'height': height,
            'markers': []
        }
        
        return UploadResponse(
            session_id=session_id,
            width=width,
            height=height,
            filename=filename
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/image/{session_id}")
async def get_image(session_id: str):
    """Retrieve the current image (with markers) for display."""
    session = get_or_recover_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        image_bytes = draw_markers_on_image(session['original_path'], session['markers'])
        return StreamingResponse(
            iter([image_bytes]),
            media_type='image/png'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving image: {str(e)}")


@router.post("/markers/{session_id}", response_model=MarkerResponse)
async def add_marker(session_id: str, marker: MarkerData):
    """Add a marker at the specified coordinates."""
    session = get_or_recover_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        x = marker.x
        y = marker.y
        
        # Validate coordinates are within image bounds
        if x < 0 or x > session['width'] or y < 0 or y > session['height']:
            raise HTTPException(status_code=400, detail="Coordinates outside image bounds")
        
        # Add marker
        session['markers'].append((x, y))
        persist_marker(session_id, x, y)
        
        return MarkerResponse(
            success=True,
            marker_count=len(session['markers']),
            markers=session['markers']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding marker: {str(e)}")


@router.get("/markers/{session_id}")
async def get_markers(session_id: str):
    """Get all markers for a session."""
    session = get_or_recover_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        'markers': session['markers'],
        'count': len(session['markers'])
    }


@router.delete("/markers/{session_id}", response_model=SessionResponse)
async def clear_markers(session_id: str):
    """Clear all markers from a session."""
    session = get_or_recover_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session['markers'] = []
    replace_persisted_markers(session_id, [])
    return SessionResponse(success=True, message='All markers cleared')


@router.delete("/markers/{session_id}/last", response_model=MarkerResponse)
async def remove_last_marker(session_id: str):
    """Remove the last added marker (undo)."""
    session = get_or_recover_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session['markers']:
        session['markers'].pop()
        replace_persisted_markers(session_id, session['markers'])
    
    return MarkerResponse(
        success=True,
        marker_count=len(session['markers']),
        markers=session['markers']
    )


@router.delete("/markers/{session_id}/{marker_index}", response_model=MarkerResponse)
async def remove_marker_at_index(session_id: str, marker_index: int):
    """Remove a marker by its exact index."""
    session = get_or_recover_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if marker_index < 0 or marker_index >= len(session['markers']):
        raise HTTPException(status_code=400, detail="Marker index out of range")

    session['markers'].pop(marker_index)
    replace_persisted_markers(session_id, session['markers'])

    return MarkerResponse(
        success=True,
        marker_count=len(session['markers']),
        markers=session['markers']
    )


@router.get("/download/{session_id}")
async def download_image(session_id: str):
    """Download the current image with markers."""
    session = get_or_recover_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        image_bytes = draw_markers_on_image(session['original_path'], session['markers'])
        
        # Generate output filename
        base_name = session['original_filename'].rsplit('.', 1)[0]
        output_filename = f'{base_name}_marked.png'
        
        return StreamingResponse(
            iter([image_bytes]),
            media_type='image/png',
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading image: {str(e)}")


@router.delete("/session/{session_id}", response_model=SessionResponse)
async def clear_session(session_id: str):
    """Clear a session and remove temporary files."""
    session = get_or_recover_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Remove temporary file
        cleanup_session_files(session['original_path'])
        
        # Remove session
        sessions.pop(session_id, None)
        replace_persisted_markers(session_id, [])
        
        return SessionResponse(success=True, message='Session cleared')
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")


@router.post("/generate/from-marker")
async def generate_detail_from_marker(
    request: MarkerDetailGenerationRequest,
    session_id: str = Query(...),
    db = Depends(get_db)
):
    """Generate a detail image centered on a precise marker coordinate."""
    session = get_or_recover_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Please upload the image again.")

    marker_index = request.marker_index

    try:
        if marker_index >= 0 and marker_index < len(session['markers']):
            marker = tuple(session['markers'][marker_index])
        elif request.x is not None and request.y is not None:
            marker = (request.x, request.y)
            if marker not in session['markers']:
                session['markers'].append(marker)
                persist_marker(session_id, marker[0], marker[1])
        else:
            raise HTTPException(
                status_code=400,
                detail="Marker coordinates missing. Place a red marker on the image before generating."
            )

        x, y = marker
        if x < 0 or x >= session['width'] or y < 0 or y >= session['height']:
            raise HTTPException(status_code=400, detail="Marker coordinates are outside the image bounds.")

        marker_region = crop_marker_region_image(session['original_path'], marker)
        vision_context = model_manager.analyze_image(marker_region)
        context_summary = summarize_marker_context(marker, vision_context)
        image_data = create_marker_detail_image(
            session['original_path'],
            marker,
            context_summary
        )

        order_index = db.query(GeneratedImage).filter(
            GeneratedImage.session_id == session_id
        ).count()

        generated_image = GeneratedImage(
            session_id=session_id,
            image_path="",
            image_data=image_data,
            prompt=f"Marker {marker_index + 1}: {context_summary}",
            model_name=f"marker-detail+{vision_context.get('model', model_manager.config.vision_model) if isinstance(vision_context, dict) else model_manager.config.vision_model}",
            order_index=order_index,
            created_at=datetime.utcnow()
        )

        db.add(generated_image)

        session_history = db.query(SessionHistory).filter(
            SessionHistory.session_id == session_id
        ).first()

        if not session_history:
            session_history = SessionHistory(session_id=session_id)
            db.add(session_history)

        session_history.total_images = order_index + 1
        session_history.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(generated_image)

        return {
            "success": True,
            "image_id": generated_image.id,
            "marker_index": marker_index,
            "marker": {"x": marker[0], "y": marker[1]},
            "vision_context": vision_context,
            "message": "Marker detail image generated"
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        db.rollback()
        logger.error(f"Error generating marker detail image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def summarize_marker_context(marker: tuple[int, int], vision_context: object) -> str:
    """Convert vision-model output into concise text for the generated detail image."""
    x, y = marker
    if not isinstance(vision_context, dict):
        return f"Detailed marker-focused view at exact coordinate ({x}, {y})."

    if vision_context.get("error"):
        return f"Detailed marker-focused view at exact coordinate ({x}, {y}). Vision context unavailable."

    model = vision_context.get("model", "vision model")
    parts = [f"Vision context from {model} for exact marker coordinate ({x}, {y})."]

    if "width" in vision_context and "height" in vision_context:
        parts.append(f"Marked crop size: {vision_context['width']} x {vision_context['height']} pixels.")
    if "dominant_channel" in vision_context:
        parts.append(f"Dominant color channel near marker: {vision_context['dominant_channel']}.")
    if "brightness" in vision_context:
        parts.append(f"Local brightness score: {vision_context['brightness']}.")
    if "detection_count" in vision_context:
        parts.append(f"Objects detected near marker: {vision_context['detection_count']}.")
    if "confidence_scores" in vision_context and vision_context["confidence_scores"]:
        score = vision_context["confidence_scores"][0]
        parts.append(f"Top confidence signal: {round(float(score), 4)}.")

    return " ".join(parts)


# ============================================================================
# New Endpoints (AI Image Generation)
# ============================================================================

@router.post("/generate/start")
async def start_generation(
    session_id: str = Query(...),
    prompts: List[str] = Query(...),
    interval: float = Query(5.0),
    max_images: Optional[int] = Query(None),
    db = Depends(get_db)
):
    """
    Start infinite image generation loop
    
    Args:
        session_id: Session ID to store images
        prompts: List of prompts to cycle through
        interval: Delay between generations in seconds
        max_images: Maximum images to generate (None = infinite)
    """
    try:
        prompts = normalize_prompts(prompts)
        if not prompts:
            raise HTTPException(status_code=400, detail="At least one prompt is required")

        if session_id in generation_tasks:
            raise HTTPException(status_code=400, detail="Generation already running for this session")
        
        # Create or get session history
        session_history = db.query(SessionHistory).filter(
            SessionHistory.session_id == session_id
        ).first()
        
        if not session_history:
            session_history = SessionHistory(
                session_id=session_id,
                drill_mode=False
            )
            db.add(session_history)
            db.commit()
        
        task = asyncio.create_task(
            run_generation_task(
                session_id=session_id,
                prompts=prompts,
                interval=interval,
                max_images=max_images,
            )
        )

        generation_tasks[session_id] = {
            "status": "running",
            "started_at": datetime.utcnow(),
            "prompts": prompts,
            "task": task
        }

        task.add_done_callback(lambda _task: generation_tasks.pop(session_id, None))

        logger.info(f"Started generation for session {session_id}")
        
        return {
            "success": True,
            "message": "Image generation started",
            "session_id": session_id,
            "prompts_count": len(prompts)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/stop")
async def stop_generation(
    session_id: str = Query(...),
    db = Depends(get_db)
):
    """Stop generation for a session"""
    try:
        task_info = generation_tasks.get(session_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="No active generation for this session")
        
        task_info["status"] = "stopped"
        task = task_info.get("task")
        if task and not task.done():
            task.cancel()
        generation_tasks.pop(session_id, None)
        
        logger.info(f"Stopped generation for session {session_id}")
        
        return {
            "success": True,
            "message": "Generation stopped",
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate/status")
async def get_generation_status(session_id: str = Query(...)):
    """Get generation status for a session"""
    task_info = generation_tasks.get(session_id)
    if not task_info:
        return {"session_id": session_id, "status": "stopped"}

    return {
        "session_id": session_id,
        "status": task_info["status"],
        "started_at": task_info["started_at"].isoformat(),
        "prompts": task_info["prompts"],
    }


@router.get("/generated-images/{session_id}")
async def get_generated_images(
    session_id: str,
    page: int = Query(0, ge=0),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db = Depends(get_db)
):
    """Get paginated generated images for a session"""
    try:
        gen_service = ImageGenerationService(db, model_manager)
        images, total_count = gen_service.get_images_for_session(
            session_id, page, page_size
        )
        
        return {
            "session_id": session_id,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size,
            "images": [
                {
                    "id": img.id,
                    "order_index": img.order_index,
                    "prompt": img.prompt,
                    "model": img.model_name,
                    "created_at": img.created_at.isoformat()
                }
                for img in images
            ]
        }
    
    except Exception as e:
        logger.error(f"Error retrieving images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generated-image/{image_id}/data")
async def get_generated_image_data(
    image_id: int,
    db = Depends(get_db)
):
    """Get image data by ID"""
    try:
        gen_service = ImageGenerationService(db, model_manager)
        image = gen_service.get_image_by_id(image_id)
        
        if not image or not image.image_data:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return StreamingResponse(
            iter([image.image_data]),
            media_type='image/png'
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving image data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Deterministic Drill Endpoints
# ============================================================================

@router.post("/drill/create")
async def create_deterministic_drill(
    session_id: str = Query(...),
    drill_name: str = Query(...),
    seed: int = Query(...),
    prompts: List[str] = Query(...),
    num_images: int = Query(10, ge=1, le=100),
    db = Depends(get_db)
):
    """
    Create a deterministic drill with fixed seed for reproducibility
    
    Args:
        session_id: Session ID
        drill_name: Name of the drill
        seed: Seed for deterministic generation
        prompts: List of prompts
        num_images: Number of images to generate
    """
    try:
        prompts = normalize_prompts(prompts)
        if not prompts:
            raise HTTPException(status_code=400, detail="At least one prompt is required")

        drill_service = DeterministicDrill(db, model_manager)
        
        # Create drill asynchronously
        drill = await drill_service.create_drill(
            session_id=session_id,
            drill_name=drill_name,
            seed=seed,
            prompts=prompts,
            num_images=num_images
        )
        
        if not drill:
            raise HTTPException(status_code=500, detail="Failed to create drill")
        
        # Update session history
        session_history = db.query(SessionHistory).filter(
            SessionHistory.session_id == session_id
        ).first()
        
        if session_history:
            session_history.drill_mode = True
            session_history.drill_seed = seed
            session_history.total_images = num_images
            db.commit()
        
        logger.info(f"Created drill '{drill_name}' with seed {seed}")
        
        return {
            "success": True,
            "drill_id": drill.id,
            "drill_name": drill.drill_name,
            "seed": drill.drill_seed,
            "num_images": num_images,
            "message": "Drill created successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating drill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drill/{drill_id}/recreate")
async def recreate_drill(
    drill_id: int,
    db = Depends(get_db)
):
    """Recreate a saved drill using the same seed"""
    try:
        drill_service = DeterministicDrill(db, model_manager)
        success = await drill_service.recreate_drill(drill_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Drill not found")
        
        return {
            "success": True,
            "drill_id": drill_id,
            "message": "Drill can be recreated using the saved seed"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recreating drill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drills/{session_id}")
async def list_session_drills(
    session_id: str,
    db = Depends(get_db)
):
    """List all drills for a session"""
    try:
        drills = db.query(SavedDrill).filter(
            SavedDrill.session_id == session_id
        ).order_by(SavedDrill.created_at.desc()).all()
        
        return {
            "session_id": session_id,
            "drill_count": len(drills),
            "drills": [
                {
                    "id": drill.id,
                    "name": drill.drill_name,
                    "seed": drill.drill_seed,
                    "description": drill.description,
                    "created_at": drill.created_at.isoformat()
                }
                for drill in drills
            ]
        }
    
    except Exception as e:
        logger.error(f"Error listing drills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Vision Analysis Endpoints
# ============================================================================

@router.post("/analyze/image/{image_id}")
async def analyze_generated_image(
    image_id: int,
    db = Depends(get_db)
):
    """Analyze a generated image with the vision model"""
    try:
        gen_service = ImageGenerationService(db, model_manager)
        image = gen_service.get_image_by_id(image_id)
        
        if not image or not image.image_data:
            raise HTTPException(status_code=404, detail="Image not found")
        
        vision_service = VisionAnalysisService(db, model_manager)
        result = vision_service.analyze_image(image_id, image.image_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        logger.info(f"Analyzed image {image_id}")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{image_id}")
async def get_image_analysis(
    image_id: int,
    db = Depends(get_db)
):
    """Retrieve analysis for an image"""
    try:
        vision_service = VisionAnalysisService(db, model_manager)
        result = vision_service.get_analysis_for_image(image_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyses/{session_id}")
async def get_session_analyses(
    session_id: str,
    limit: int = Query(10, ge=1, le=100),
    db = Depends(get_db)
):
    """Get latest analyses for a session"""
    try:
        vision_service = VisionAnalysisService(db, model_manager)
        analyses = vision_service.get_latest_analyses(session_id, limit)
        
        return {
            "session_id": session_id,
            "analysis_count": len(analyses),
            "analyses": analyses
        }
    
    except Exception as e:
        logger.error(f"Error retrieving analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# History & Navigation Endpoints
# ============================================================================

@router.get("/session/{session_id}/history")
async def get_session_history(
    session_id: str,
    db = Depends(get_db)
):
    """Get session history"""
    try:
        session_history = db.query(SessionHistory).filter(
            SessionHistory.session_id == session_id
        ).first()
        
        if not session_history:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_history.session_id,
            "current_image_index": session_history.current_image_index,
            "total_images": session_history.total_images,
            "drill_mode": session_history.drill_mode,
            "drill_seed": session_history.drill_seed,
            "created_at": session_history.created_at.isoformat(),
            "updated_at": session_history.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/session/{session_id}/navigate")
async def navigate_session(
    session_id: str,
    image_index: int = Query(..., ge=0),
    db = Depends(get_db)
):
    """Navigate to a specific image in the session"""
    try:
        session_history = db.query(SessionHistory).filter(
            SessionHistory.session_id == session_id
        ).first()
        
        if not session_history:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Validate index
        if image_index >= session_history.total_images:
            raise HTTPException(status_code=400, detail="Image index out of range")
        
        session_history.current_image_index = image_index
        session_history.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Navigated session {session_id} to image {image_index}")
        
        return {
            "success": True,
            "session_id": session_id,
            "current_image_index": image_index
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error navigating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/reset")
async def reset_session(
    session_id: str,
    db = Depends(get_db)
):
    """Reset session to initial state"""
    try:
        session_history = db.query(SessionHistory).filter(
            SessionHistory.session_id == session_id
        ).first()
        
        if not session_history:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_history.current_image_index = 0
        session_history.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Reset session {session_id}")
        
        return {
            "success": True,
            "message": "Session reset to initial state",
            "session_id": session_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Model Configuration Endpoints
# ============================================================================

@router.get("/models/config")
async def get_models_config():
    """Get current model configuration"""
    return {
        "success": True,
        "config": model_manager.get_config()
    }


@router.put("/models/image-generation")
async def set_image_generation_model(
    model_name: str = Query(...),
    api_key: Optional[str] = Query(None)
):
    """Change image generation model"""
    try:
        model_manager.set_image_generation_model(model_name, api_key)
        
        logger.info(f"Changed image generation model to {model_name}")
        
        return {
            "success": True,
            "message": f"Image generation model changed to {model_name}",
            "model": model_name
        }
    
    except Exception as e:
        logger.error(f"Error changing model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/models/vision")
async def set_vision_model(
    model_name: str = Query(...),
    model_path: Optional[str] = Query(None)
):
    """Change vision model"""
    try:
        model_manager.set_vision_model(model_name, model_path)
        
        logger.info(f"Changed vision model to {model_name}")
        
        return {
            "success": True,
            "message": f"Vision model changed to {model_name}",
            "model": model_name
        }
    
    except Exception as e:
        logger.error(f"Error changing model: {e}")
        raise HTTPException(status_code=500, detail=str(e))
