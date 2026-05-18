# Red Marker - Image Annotation Tool

A professional, production-ready web application for annotating images with red ring markers. Built with FastAPI and modern web standards.

## Features

✨ **Key Features:**
- 🖼️ Upload images (JPG, PNG, GIF, WebP)
- 🖱️ Click to mark locations with red ring markers
- ↶ Undo/Remove individual markers
- 🗑️ Clear all markers at once
- ⬇️ Download marked image
- 📱 Responsive design for desktop and mobile
- 🔒 Secure file handling with validation
- ⚡ High-performance FastAPI backend

## Technology Stack

- **Backend:** FastAPI 0.115.6 - Modern async Python web framework
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Image Processing:** PIL/Pillow 10.1.0
- **Server:** Uvicorn 0.32.1 - ASGI server
- **File Upload:** python-multipart 0.0.28

## Project Structure

```
Red_marker/
├── src/                          # Application source code
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI app factory
│   ├── config.py                # Configuration settings
│   ├── models.py                # Pydantic models
│   ├── utils.py                 # Utility functions
│   └── api/
│       ├── __init__.py
│       └── routes.py            # API endpoints
│
├── static/                       # Frontend assets
│   ├── index.html               # Main HTML page
│   ├── css/
│   │   └── style.css            # Styling
│   └── js/
│       └── script.js            # Frontend logic
│
├── temp/                         # Temporary image storage
│   └── .gitkeep
│
├── run.py                        # Application entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone or Navigate to Project
```bash
cd /Users/sshah/Red_marker
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python run.py
```

Or use uvicorn directly:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 5000
```

The application will start on **http://localhost:5000**

## Usage

1. **Open the Application**
   - Navigate to http://localhost:5000 in your web browser

2. **Upload an Image**
   - Click the upload area or drag and drop an image
   - Supported formats: JPG, PNG, GIF, WebP (max 50MB)

3. **Mark Locations**
   - Click anywhere on the displayed image to add a marker
   - Each click adds a red ring marker at that coordinate

4. **View Markers**
   - See the list of all markers in the info panel
   - Each marker shows its coordinates (#index: x, y)

5. **Remove Markers**
   - Click "Undo" to remove the last marker
   - Click "Remove" next to a specific marker in the list
   - Click "Clear All" to remove all markers

6. **Download**
   - Click "Download" to download the marked image as PNG
   - The file is saved as `[filename]_marked.png`

7. **Start Over**
   - Click "New Image" to upload a different image

## API Endpoints

All endpoints are prefixed with `/api`

### POST `/api/upload`
Upload an image file.
- **Request:** FormData with `file` field
- **Response:** `{ session_id, width, height, filename }`

### GET `/api/image/{session_id}`
Retrieve the current image with markers (PNG format).
- **Response:** PNG image stream

### POST `/api/markers/{session_id}`
Add a marker at coordinates.
- **Request:** `{ x, y }` (JSON)
- **Response:** `{ success, marker_count, markers }`

### GET `/api/markers/{session_id}`
Get all markers for a session.
- **Response:** `{ markers, count }`

### DELETE `/api/markers/{session_id}`
Clear all markers from a session.
- **Response:** `{ success, message }`

### GET `/api/download/{session_id}`
Download the marked image.
- **Response:** PNG image file (with attachment header)

### DELETE `/api/session/{session_id}`
Clear a session and remove temporary files.
- **Response:** `{ success, message }`

### GET `/health`
Health check endpoint.
- **Response:** `{ status, service }`

## Configuration

Configuration is managed in `src/config.py`. Key settings:

```python
# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / 'temp'
STATIC_DIR = BASE_DIR / 'static'

# Image settings
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Marker settings
MARKER_RADIUS = 15  # pixels (diameter ~30px)
MARKER_COLOR = 'red'
MARKER_WIDTH = 2  # stroke width

# Server settings
HOST = '0.0.0.0'
PORT = 5000
DEBUG = False
```

## API Documentation

Interactive API documentation is automatically generated:

- **Swagger UI:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc

## Code Structure

### `src/main.py`
FastAPI application factory. Creates and configures the app with middleware, routes, and error handlers.

### `src/config.py`
Centralized configuration management. All settings in one place for easy maintenance.

### `src/models.py`
Pydantic models for request/response validation. Provides type safety and automatic documentation.

### `src/api/routes.py`
API endpoint handlers. All route logic organized in one module.

### `src/utils.py`
Utility functions for image processing and file handling. Reusable helpers extracted for maintainability.

## Error Handling

Comprehensive error handling with proper HTTP status codes:

- ✅ 400: Bad Request (invalid file, coordinates out of bounds)
- ✅ 404: Not Found (missing session, endpoint not found)
- ✅ 500: Internal Server Error (processing failures)
- ✅ 200: Success (successful operations)

## Performance Considerations

- **FastAPI:** High performance async Python framework
- **In-memory sessions:** Fast session data retrieval
- **PIL/Pillow:** Efficient image processing
- **Vanilla JS:** No framework overhead

### Latency Factors:
- **Primary:** Image file size and network bandwidth
- **Secondary:** Image dimensions (larger = slower processing)

**Optimization tips:**
- Upload images under 3MB
- Prefer JPG/WebP over PNG
- Use reasonably-sized images (2000x2000px or less)

## Browser Support

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Security Features

- ✅ Filename validation and sanitization
- ✅ File type validation (client & server)
- ✅ File size limits to prevent DoS
- ✅ Session-based temporary file storage
- ✅ Automatic cleanup of session data
- ✅ CORS middleware for cross-origin safety

## Troubleshooting

### "Address already in use" Error
```bash
# Change the port in src/config.py
PORT = 5001
```

### Module Not Found Errors
```bash
# Ensure dependencies are installed
pip install -r requirements.txt
```

### Image Not Displaying
- Check browser console for errors (F12)
- Ensure image format is supported
- Try a different image file
- Clear browser cache and refresh

### Markers Not Appearing
- Check clicks are within image bounds
- Ensure JavaScript is enabled
- Check browser console for errors

## Deployment

### Production with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000 src.main:app
```

### Using Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

### Using Nginx (Reverse Proxy)
```nginx
upstream red_marker {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://red_marker;
    }
}
```

## Development

### Adding New Endpoints
1. Add route to `src/api/routes.py`
2. Add Pydantic model to `src/models.py` if needed
3. Add utility functions to `src/utils.py` if needed

### Testing
```bash
# Run with uvicorn in reload mode for development
uvicorn src.main:app --reload
```

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review browser console errors (F12)
3. Check server logs
4. Review interactive API docs at http://localhost:5000/docs
5. Verify all dependencies are installed

---

**Happy marking!** 🔴


## Usage

1. **Open the Application**
   - Navigate to `http://localhost:5000` in your web browser

2. **Upload an Image**
   - Click the upload area or drag and drop an image file
   - Supported formats: JPG, PNG, GIF, WebP (max 50MB)

3. **Mark Locations**
   - Click anywhere on the displayed image to add a red ring marker
   - Each click adds a marker at that exact coordinate

4. **View Markers**
   - See the list of all markers in the info panel
   - Each marker shows its coordinates (#index: x, y)

5. **Remove Markers**
   - Click "Undo" to remove the last marker
   - Click "Remove" next to a specific marker in the list
   - Click "Clear All" to remove all markers

6. **Download**
   - Click "Download" to download the marked image as PNG
   - The file is saved as `[filename]_marked.png`

7. **Start Over**
   - Click "New Image" to upload a different image

## API Endpoints

### POST `/api/upload`
Upload an image file.
- **Request:** FormData with `file` field
- **Response:** `{ session_id, width, height, filename }`

### GET `/api/image/<session_id>`
Retrieve the current image with markers (PNG format).

### POST `/api/markers/<session_id>`
Add a marker at coordinates.
- **Request:** `{ x, y }` (JSON)
- **Response:** `{ success, marker_count, markers }`

### GET `/api/markers/<session_id>`
Get all markers for a session.
- **Response:** `{ markers, count }`

### DELETE `/api/markers/<session_id>`
Clear all markers from a session.
- **Response:** `{ success, message }`

### GET `/api/download/<session_id>`
Download the marked image.
- **Response:** PNG image file (with attachment header)

### DELETE `/api/session/<session_id>`
Clear a session and remove temporary files.
- **Response:** `{ success, message }`

## Configuration

### Image Settings (in `app.py`)
- `MAX_FILE_SIZE`: Maximum file upload size (default: 50MB)
- `MARKER_RADIUS`: Circle radius in pixels (default: 15px → ~30px diameter)
- `MARKER_COLOR`: Marker color (default: 'red')
- `MARKER_WIDTH`: Stroke width in pixels (default: 2)

### Server Settings (in `app.py`)
- `HOST`: Server host (default: 0.0.0.0 - all interfaces)
- `PORT`: Server port (default: 5000)

To change these, edit the bottom of `app.py`:
```python
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
```

## Error Handling

The application includes comprehensive error handling:

- ✅ File type validation
- ✅ File size validation
- ✅ Coordinate boundary checking
- ✅ Session validation
- ✅ Image format validation
- ✅ Graceful error messages
- ✅ HTTPException-based responses with proper status codes

## Performance Considerations

- FastAPI provides high performance with async support
- Images are processed in-memory for speed
- Temporary files are cleaned up when sessions end
- Canvas overlay uses GPU acceleration where available
- Responsive design optimized for all screen sizes

## Browser Support

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Security Features

- Filename validation and handling
- File type validation on both client and server
- File size limits to prevent DoS attacks
- Session-based temporary file storage
- Automatic cleanup of session data
- CORS middleware configured for safety

## Troubleshooting

### "Address already in use" Error
The port 5000 is already in use. Change the port:
```python
uvicorn.run(app, host='0.0.0.0', port=5001)
```

### Module Not Found Errors
Ensure dependencies are installed:
```bash
pip install -r requirements.txt
```

### Image Not Displaying
- Check browser console for errors (F12)
- Ensure image format is supported
- Try a different image file
- Clear browser cache and refresh

### Markers Not Appearing
- Check that clicks are within image bounds
- Ensure JavaScript is enabled in browser
- Check browser console for errors

## Performance Tips

- Use JPG format for photo images (smaller file size)
- Use PNG format for screenshots and graphics
- Optimize images before uploading for faster processing
- Clear the `temp/` folder periodically for cleanup

## Deployment

For production deployment:

1. Use `debug=False` (default in uvicorn production)
2. Use a production ASGI server (Gunicorn with Uvicorn workers)
3. Set up a reverse proxy (Nginx, Apache)
4. Use HTTPS/TLS
5. Implement file size and rate limiting
6. Set up automated temp folder cleanup

### Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000 app:app
```

## Why FastAPI?

FastAPI offers several advantages over Flask:

- **Async/await support** - Better handling of I/O operations
- **Automatic API documentation** - Interactive Swagger UI at `/docs`
- **Type hints** - Built-in validation with Pydantic models
- **Performance** - Comparable to NodeJS/Go for speed
- **Modern Python** - Uses Python 3.6+ features
- **JSON Schema** - Automatic JSON schema generation
- **Dependency injection** - Built-in dependency system

## Documentation

Access the interactive API documentation:
- **Swagger UI:** `http://localhost:5000/docs`
- **ReDoc:** `http://localhost:5000/redoc`

These are automatically generated from your API code.

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review browser console errors (F12)
3. Check server terminal output
4. Verify all dependencies are installed
5. Check the interactive API docs at `/docs`

---

**Happy marking!** 🔴
# Red_Marker
