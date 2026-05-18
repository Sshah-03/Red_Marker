"""
Configuration settings for Red Marker application
"""

from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / 'temp'
STATIC_DIR = BASE_DIR / 'static'
DB_DIR = BASE_DIR / 'data'

# Ensure directories exist
TEMP_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# Image configuration
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Marker configuration
MARKER_RADIUS = 15  # pixels (diameter ~30px)
MARKER_COLOR = 'red'
MARKER_WIDTH = 2  # stroke width

# Server configuration
HOST = '0.0.0.0'
PORT = 5000
DEBUG = False

# API configuration
API_TITLE = 'Red Marker API'
API_VERSION = '1.0.0'
API_DESCRIPTION = 'Image annotation tool with red ring markers and AI generation'

# Database configuration
DATABASE_URL = f"sqlite:///{DB_DIR}/red_marker.db"

# Model configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
IMAGE_GENERATION_MODEL = "gemini-1.5-pro"
VISION_MODEL = "resnet50"  # Options: resnet50, clip, yolo, custom

# Image generation configuration
IMAGE_SIZE = (512, 512)
MAX_GENERATION_RETRIES = 3
GENERATION_TIMEOUT = 60  # seconds

# Generation loop configuration
DEFAULT_GENERATION_INTERVAL = 5.0  # seconds between generations
DEFAULT_MAX_IMAGES = None  # None = infinite

# Pagination configuration
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Logging configuration
LOG_LEVEL = "INFO"
