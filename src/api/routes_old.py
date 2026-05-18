"""
API route handlers for Red Marker application
"""

import os
import uuid
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse

from src.models import MarkerData, UploadResponse, MarkerResponse, SessionResponse
from src.config import TEMP_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from src.utils import (
    allowed_file, validate_image, draw_markers_on_image, cleanup_session_files
)

router = APIRouter(prefix="/api", tags=["api"])

# Global session storage (in-memory)
sessions = {}


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
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
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
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        x = marker.x
        y = marker.y
        
        session = sessions[session_id]
        
        # Validate coordinates are within image bounds
        if x < 0 or x > session['width'] or y < 0 or y > session['height']:
            raise HTTPException(status_code=400, detail="Coordinates outside image bounds")
        
        # Add marker
        session['markers'].append((x, y))
        
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
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        'markers': session['markers'],
        'count': len(session['markers'])
    }


@router.delete("/markers/{session_id}", response_model=SessionResponse)
async def clear_markers(session_id: str):
    """Clear all markers from a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[session_id]['markers'] = []
    return SessionResponse(success=True, message='All markers cleared')


@router.get("/download/{session_id}")
async def download_image(session_id: str):
    """Download the current image with markers."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
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
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    try:
        # Remove temporary file
        cleanup_session_files(session['original_path'])
        
        # Remove session
        del sessions[session_id]
        
        return SessionResponse(success=True, message='Session cleared')
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")
