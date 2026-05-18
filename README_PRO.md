# Red Marker Pro - Advanced Image Annotation with AI

A comprehensive web application for image annotation with integrated AI image generation and vision analysis capabilities.

## 🌟 Features

### Core Features
- **Image Annotation**: Click to place red ring markers on images
- **Undo/Clear**: Remove markers individually or all at once
- **Download**: Export annotated images
- **Session Management**: Persistent session tracking

### AI Image Generation
- **Infinite Generation Loop**: Continuously generate images using Gemini API
- **Configurable Prompts**: Multiple prompts cycled during generation
- **Deterministic Drills**: Create reproducible image sets using seeds
- **Pagination**: Browse through generated images with next/previous controls
- **Background Tasks**: Generation runs asynchronously in the background

### Vision Analysis
- **Multiple Models**: ResNet50, CLIP, YOLOv8, or custom models
- **Local Processing**: Analyze images on your machine
- **Confidence Scores**: Get confidence metrics for analyses
- **Batch Analysis**: Analyze multiple images at once
- **Result Storage**: All analyses saved to database

### History & Navigation
- **Session History**: Track navigation through image collections
- **Pagination Support**: Next page, previous page navigation
- **Go To Image**: Jump to specific image by index
- **Reset Function**: Reset session to initial state
- **Navigation Tracking**: View complete navigation history

### Model Configuration
- **Flexible Model Selection**: Switch between different image generation models
- **Vision Model Switching**: Change vision models on the fly
- **Custom Models**: Support for loading custom model implementations
- **API Key Management**: Secure API key input for authentication
- **Live Configuration**: Changes take effect immediately

## 🚀 Getting Started

### Installation

1. **Clone the repository**
   ```bash
   cd /Users/sshah/Red_marker
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

5. **Initialize database**
   ```bash
   python -c "from src.database import init_db; init_db()"
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   - Open browser and navigate to `http://localhost:5000`

### Configuration

Edit `src/config.py` to customize:
- Port and host
- Default image size
- Generation timeout
- Pagination settings
- Default models

## 📱 UI Tabs

### 1. Upload & Annotate
- Upload images
- Click to place markers
- Manage markers with undo/clear
- Download annotated images

### 2. AI Generation
- Configure generation prompts
- Set generation interval
- Create deterministic drills
- View and manage generated images
- Pagination through results

### 3. History & Navigation
- View session information
- Navigate between images
- Jump to specific images
- View navigation history
- Reset to start

### 4. Vision Analysis
- Analyze individual images
- View analysis results
- Browse session analyses
- Compare analyses across images

### 5. Model Config
- View current configuration
- Switch image generation models
- Switch vision models
- Provide API keys
- Configure custom models

## 🔧 API Endpoints

### Original Endpoints
- `POST /api/upload` - Upload image
- `GET /api/image/{session_id}` - Get image with markers
- `POST /api/markers/{session_id}` - Add marker
- `GET /api/markers/{session_id}` - Get all markers
- `DELETE /api/markers/{session_id}` - Clear markers
- `GET /api/download/{session_id}` - Download annotated image

### Generation Endpoints
- `POST /api/generate/start` - Start generation loop
- `POST /api/generate/stop` - Stop generation
- `GET /api/generated-images/{session_id}` - Get paginated images
- `GET /api/generated-image/{image_id}/data` - Get image data

### Drill Endpoints
- `POST /api/drill/create` - Create deterministic drill
- `GET /api/drill/{drill_id}/recreate` - Recreate drill with same seed
- `GET /api/drills/{session_id}` - List all drills

### Analysis Endpoints
- `POST /api/analyze/image/{image_id}` - Analyze image
- `GET /api/analysis/{image_id}` - Get analysis results
- `GET /api/analyses/{session_id}` - Get session analyses

### History Endpoints
- `GET /api/session/{session_id}/history` - Get session history
- `PUT /api/session/{session_id}/navigate` - Navigate to image
- `POST /api/session/{session_id}/reset` - Reset session

### Model Endpoints
- `GET /api/models/config` - Get current configuration
- `PUT /api/models/image-generation` - Change image generation model
- `PUT /api/models/vision` - Change vision model

## 📊 Database Schema

### GeneratedImage
- id: Primary key
- session_id: Session identifier
- image_data: Binary image data
- prompt: Generation prompt
- model_name: Model used
- order_index: Position in sequence

### VisionAnalysis
- id: Primary key
- image_id: Reference to GeneratedImage
- model_name: Vision model used
- analysis_result: Analysis results (JSON)
- confidence_score: Confidence metric

### SessionHistory
- session_id: Primary key
- current_image_index: Current position
- total_images: Total images in session
- drill_mode: Is deterministic drill
- drill_seed: Seed if drill

### SavedDrill
- id: Primary key
- session_id: Reference to session
- drill_name: User-friendly name
- drill_seed: Fixed seed for reproducibility
- image_ids: IDs of generated images

### MarkerAnnotation
- id: Primary key
- session_id: Session identifier
- x, y: Marker coordinates
- created_at: Timestamp

## 🤖 Supported Models

### Image Generation
- **Gemini 1.5 Pro** - Latest high-quality generation
- **Gemini 1.0 Pro Vision** - Vision-aware generation
- Custom models via API

### Vision Analysis
- **ResNet50** - Image classification (1000 classes)
- **CLIP** - Vision-language understanding
- **YOLOv8** - Object detection
- **Custom** - Load your own model

## 💡 Usage Examples

### Generate Images Continuously
1. Go to "AI Generation" tab
2. Enter prompts (one per line)
3. Set interval and max images
4. Click "Start Generation"
5. Monitor progress in "Generated Images"

### Create Deterministic Drill
1. Enter drill name and prompts
2. Set seed (same seed = same results)
3. Set number of images
4. Click "Create Drill"
5. Drill is saved and reproducible

### Analyze Images
1. Go to "Vision Analysis" tab
2. Enter image ID
3. Click "Analyze Image"
4. View results with confidence scores
5. Browse all session analyses

### Navigate Through Images
1. Go to "History & Navigation" tab
2. Use Previous/Next buttons
3. Or jump to specific image index
4. View complete navigation history
5. Reset to start when needed

### Change Models
1. Go to "Model Config" tab
2. Select new image generation model
3. Add API key if needed
4. Select new vision model
5. Changes take effect immediately

## 🔐 Security Considerations

- API keys should be set via environment variables
- Don't hardcode sensitive credentials
- Database is local SQLite by default
- Use environment variables for configuration
- Validate all user inputs

## 📝 Configuration Options

### config.py Settings
```python
# Database
DATABASE_URL = "sqlite:///data/red_marker.db"

# Models
IMAGE_GENERATION_MODEL = "gemini-1.5-pro"
VISION_MODEL = "resnet50"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Generation
DEFAULT_GENERATION_INTERVAL = 5.0
DEFAULT_MAX_IMAGES = None  # None = infinite

# Pagination
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
```

## 🐛 Troubleshooting

### Gemini API Issues
- Ensure `GEMINI_API_KEY` is set correctly
- Check API key has image generation permissions
- Verify API quota and rate limits

### Vision Model Issues
- Install required packages: `pip install torch torchvision`
- For CLIP: `pip install openai-clip`
- For YOLO: `pip install ultralytics`

### Database Issues
- Delete `data/red_marker.db` to reset database
- Check database directory exists
- Verify SQLAlchemy is installed

### Frontend Issues
- Clear browser cache
- Check browser console for errors
- Verify all JavaScript files are loaded

## 📦 Project Structure

```
Red_marker/
├── app.py              # Original FastAPI app
├── run.py              # Application entry point
├── requirements.txt    # Python dependencies
├── src/
│   ├── main.py         # App factory
│   ├── config.py       # Configuration
│   ├── database.py     # Database models
│   ├── model_loader.py # Model management
│   ├── services.py     # Generation service
│   ├── vision_service.py # Vision analysis
│   ├── models.py       # Pydantic models
│   └── api/
│       ├── routes.py   # Original routes
│       └── routes_enhanced.py # New routes
├── static/
│   ├── index.html      # Main HTML
│   ├── css/style.css   # Styling
│   └── js/
│       ├── script.js   # Core logic
│       ├── generation.js # Generation UI
│       ├── analysis.js # Analysis UI
│       ├── history.js  # Navigation UI
│       └── models.js   # Model config UI
├── temp/               # Temporary files
└── data/               # Database directory
```

## 🚀 Performance Tips

1. **Reduce Generation Interval**: For faster generation, decrease interval
2. **Limit Concurrent Operations**: Don't run too many analyses simultaneously
3. **Use Local Models**: Local vision models are faster than API calls
4. **Optimize Prompts**: Shorter prompts generate faster
5. **Pagination**: Load images in batches, not all at once

## 🔄 Workflow Example

1. Upload an image for annotation
2. Add markers to identify areas of interest
3. Start AI generation with diverse prompts
4. Wait for images to generate
5. Create a deterministic drill for reproducible results
6. Navigate through generated images
7. Analyze images with vision model
8. Compare results across batches
9. Download annotated or analyzed results

## 📚 Additional Resources

- Gemini API: https://ai.google.dev
- PyTorch: https://pytorch.org
- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy: https://sqlalchemy.org

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💼 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation in code
3. Check browser console for frontend errors
4. Review server logs for backend errors

---

**Version**: 2.0.0  
**Last Updated**: May 17, 2024  
**Status**: Production Ready
