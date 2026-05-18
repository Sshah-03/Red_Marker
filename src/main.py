"""
FastAPI application factory and configuration
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.config import API_TITLE, API_VERSION, API_DESCRIPTION, STATIC_DIR
from src.api.routes_enhanced import router as new_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include the enhanced router. It also contains the original annotation routes.
    app.include_router(new_router)
    
    # Serve static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    
    # Root endpoint - serve main HTML
    @app.get("/")
    async def index():
        """Serve the main HTML page."""
        return FileResponse(str(STATIC_DIR / "index.html"))
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "Red Marker API"}
    
    # Error handlers
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
    
    return app


app = create_app()
