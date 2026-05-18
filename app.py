"""
Red Marker Image Upload and Annotation Application
Backend: FastAPI application for image processing and marker placement
"""

import os
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image, ImageDraw
import io
import shutil

app = FastAPI(title="Red Marker API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_FOLDER = 'temp'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MARKER_RADIUS = 15  # pixels (diameter ~30px)
MARKER_COLOR = 'red'
MARKER_WIDTH = 2  # stroke width

# Create temp directory if it doesn't exist
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

# Store session data (image path and original filename)
sessions = {}


# Pydantic models
class MarkerData(BaseModel):
    """Model for marker coordinates"""
    x: int
    y: int


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
    markers: list = []
    message: str = ""


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Mount static files (must be done before route definitions)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


@app.post("/api/upload")
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
        
        # Validate it's a real image
        try:
            img = Image.open(io.BytesIO(content))
            width, height = img.size
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded image temporarily
        filename = file.filename
        temp_path = os.path.join(UPLOAD_FOLDER, f'{session_id}_original_{filename}')
        
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/image/{session_id}")
async def get_image(session_id: str):
    """Retrieve the current image (with markers) for display."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    try:
        # Open the original image
        img = Image.open(session['original_path']).convert('RGB')
        
        # Draw markers if any exist
        if session['markers']:
            draw = ImageDraw.Draw(img)
            for x, y in session['markers']:
                # Draw hollow circle (ring)
                left = x - MARKER_RADIUS
                top = y - MARKER_RADIUS
                right = x + MARKER_RADIUS
                bottom = y + MARKER_RADIUS
                draw.ellipse(
                    [left, top, right, bottom],
                    outline=MARKER_COLOR,
                    width=MARKER_WIDTH
                )
        
        # Convert to bytes
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        return StreamingResponse(img_io, media_type='image/png')
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving image: {str(e)}")


@app.post("/api/markers/{session_id}")
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid coordinate values")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding marker: {str(e)}")


@app.get("/api/markers/{session_id}")
async def get_markers(session_id: str):
    """Get all markers for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        'markers': session['markers'],
        'count': len(session['markers'])
    }


@app.delete("/api/markers/{session_id}")
async def clear_markers(session_id: str):
    """Clear all markers from a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[session_id]['markers'] = []
    return {'success': True, 'message': 'All markers cleared'}


@app.get("/api/download/{session_id}")
async def download_image(session_id: str):
    """Download the current image with markers."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    try:
        # Open the original image
        img = Image.open(session['original_path']).convert('RGB')
        
        # Draw markers if any exist
        if session['markers']:
            draw = ImageDraw.Draw(img)
            for x, y in session['markers']:
                # Draw hollow circle (ring)
                left = x - MARKER_RADIUS
                top = y - MARKER_RADIUS
                right = x + MARKER_RADIUS
                bottom = y + MARKER_RADIUS
                draw.ellipse(
                    [left, top, right, bottom],
                    outline=MARKER_COLOR,
                    width=MARKER_WIDTH
                )
        
        # Convert to bytes
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        # Generate output filename
        base_name = session['original_filename'].rsplit('.', 1)[0]
        output_filename = f'{base_name}_marked.png'
        
        return StreamingResponse(
            iter([img_io.getvalue()]),
            media_type='image/png',
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading image: {str(e)}")


@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a session and remove temporary files."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    try:
        # Remove temporary file
        if os.path.exists(session['original_path']):
            os.remove(session['original_path'])
        
        # Remove session
        del sessions[session_id]
        
        return {'success': True, 'message': 'Session cleared'}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found"}
    )


@app.exception_handler(500)
async def server_error_handler(request, exc):
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
