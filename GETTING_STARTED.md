# 🔴 Red Marker Pro - Getting Started Guide

## Quick Start (5 Minutes)

### 1. Set Up Environment
```bash
cd /Users/sshah/Red_marker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key
```bash
# Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Or add to .env file
echo "GEMINI_API_KEY=your-api-key-here" > .env
```

### 3. Run Application
```bash
# Option 1: Quick start with auto-setup
python quickstart.py

# Option 2: Manual start
python run.py

# Option 3: Using Uvicorn directly
uvicorn app:app --reload --port 5000
```

### 4. Access Application
- **Web Interface**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

---

## Feature Overview

### 1️⃣ Upload & Annotate
- Upload images (JPG, PNG, GIF, WebP)
- Click to place red ring markers
- Undo individual markers or clear all
- Download annotated images

**How to Use**:
1. Click "Upload & Annotate" tab
2. Click upload area to select image
3. Click on image to place markers
4. Use Undo/Clear buttons as needed
5. Click Download to save

---

### 2️⃣ AI Generation
- Generate images continuously using Gemini API
- Cycle through multiple prompts
- Create deterministic drills with fixed seeds

**How to Use - Continuous Generation**:
1. Go to "AI Generation" tab
2. Enter prompts (one per line):
   ```
   A red cat
   A blue dog
   A green bird
   ```
3. Set interval (seconds between generations)
4. Click "Start Generation"
5. Monitor in "Generated Images" section

**How to Use - Deterministic Drill**:
1. Enter drill name: "Test Drill 1"
2. Set seed: 42 (same seed = same results)
3. Set number of images: 10
4. Click "Create Drill"
5. Drill appears in "Saved Drills"
6. Click "Recreate" anytime to generate same images

**Key Concepts**:
- **Seed**: Fixed number for reproducible generation
- **Interval**: Wait time between image generations
- **Max Images**: 0 = infinite, or set a limit
- **Deterministic**: Same seed always produces same images

---

### 3️⃣ History & Navigation
- Navigate through images sequentially
- Jump to specific image by index
- View complete navigation history
- Reset session to start

**How to Use**:
1. Go to "History & Navigation" tab
2. View session info (current position, total images)
3. Use navigation buttons:
   - ← Previous: Go to previous image
   - Next →: Go to next image
   - Go To: Jump to specific index
   - ↻ Reset: Reset to first image
4. View "Navigation History" showing visited images
5. Click any history item to return to that image

**Understanding Navigation**:
- Current Index: Which image you're viewing (0-based)
- Total Images: How many images exist in session
- History: Shows timestamps of visited images

---

### 4️⃣ Vision Analysis
- Analyze images with local vision models
- Get confidence scores
- View analysis results
- Compare analyses

**How to Use**:
1. Go to "Vision Analysis" tab
2. Enter image ID: 1, 2, 3, etc.
3. Click "Analyze Image"
4. View results with confidence scores
5. Browse "Session Analyses" for all results
6. Click "View Details" to see full results

**Supported Models**:
- ResNet50: Image classification (1000 classes)
- CLIP: Vision-language understanding
- YOLOv8: Object detection
- Custom: Your own model

---

### 5️⃣ Model Configuration
- Switch image generation models at runtime
- Switch vision models at runtime
- Provide API keys when needed
- Configure custom model paths

**How to Use**:
1. Go to "Model Config" tab
2. View current configuration
3. For Image Generation:
   - Select model from dropdown
   - Add API key if needed (optional if set via env)
   - Click "Update"
4. For Vision Model:
   - Select model from dropdown
   - For custom: Add path to model file
   - Click "Update"
5. Changes take effect immediately

**Available Models**:

**Image Generation**:
- Gemini 1.5 Pro (recommended)
- Gemini 1.0 Pro Vision
- Custom

**Vision Analysis**:
- ResNet50 (lightweight, fast)
- CLIP (semantic, flexible)
- YOLOv8 (detection, accurate)
- Custom

---

## 📊 Example Workflows

### Workflow 1: Quick Image Annotation
1. Upload image
2. Click to place 5 markers
3. Download annotated image
4. Done! (2 minutes)

### Workflow 2: Generate & Analyze
1. Generate 20 images with diverse prompts
2. Analyze first 10 with vision model
3. Compare confidence scores
4. Select best images (10 minutes)

### Workflow 3: Reproducible Testing
1. Create deterministic drill with seed 42
2. Run analysis on all images
3. Create new drill with seed 100
4. Compare results between drills (15 minutes)

### Workflow 4: Interactive Navigation
1. Start generation (100 images)
2. Navigate to image 50
3. Analyze that image
4. Navigate through surrounding images
5. Jump back to start
6. Reset session (varies)

---

## 🔧 Configuration

### Environment Variables
```bash
# Required for image generation
export GEMINI_API_KEY="your-api-key"

# Optional
export ENVIRONMENT="development"
export LOG_LEVEL="INFO"
```

### Configuration File (`src/config.py`)
```python
# Models
IMAGE_GENERATION_MODEL = "gemini-1.5-pro"
VISION_MODEL = "resnet50"

# Generation
DEFAULT_GENERATION_INTERVAL = 5.0  # seconds
DEFAULT_MAX_IMAGES = None  # None = infinite

# Pagination
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
```

---

## 🐛 Troubleshooting

### Problem: "Image generation not working"
**Solution**:
- Check GEMINI_API_KEY is set: `echo $GEMINI_API_KEY`
- Verify API key is valid in Google Cloud Console
- Check API has image generation enabled
- Look for error in browser console (F12)

### Problem: "Vision model not available"
**Solution**:
- Install PyTorch: `pip install torch torchvision`
- For CLIP: `pip install openai-clip`
- For YOLO: `pip install ultralytics`
- Check model config in "Model Config" tab

### Problem: "Database errors"
**Solution**:
- Delete database: `rm -rf data/red_marker.db`
- Restart application
- Database will be recreated
- Run: `python run.py`

### Problem: "Port 5000 already in use"
**Solution**:
- Change port in `src/config.py`: `PORT = 5001`
- Or kill process: `lsof -ti:5000 | xargs kill -9`

### Problem: "Browser shows blank page"
**Solution**:
- Clear cache: Ctrl+Shift+Delete
- Check console: F12 → Console tab
- Verify server running: Check terminal
- Try incognito mode

---

## 📚 API Examples

### Generate Images
```bash
curl -X POST "http://localhost:5000/api/generate/start" \
  -G \
  -d "session_id=test-123" \
  -d "interval=5" \
  -d "max_images=10" \
  -d "prompts=A%20cat" \
  -d "prompts=A%20dog"
```

### Get Generated Images
```bash
curl "http://localhost:5000/api/generated-images/test-123?page=0&page_size=10"
```

### Analyze Image
```bash
curl -X POST "http://localhost:5000/api/analyze/image/1"
```

### Change Vision Model
```bash
curl -X PUT "http://localhost:5000/api/models/vision" \
  -G -d "model_name=yolo"
```

---

## 📱 UI Tips & Tricks

### Navigation
- **Tab Switching**: Click tab buttons to switch sections
- **Keyboard**: Use Tab key to navigate form elements
- **Mobile**: Responsive design works on tablets

### Performance
- **Pagination**: Images load in batches (faster)
- **Model Switching**: Instant without restart
- **Polling**: Only active during generation

### Organization
- **Drills**: Save configurations for reuse
- **History**: Track all navigation
- **Naming**: Name drills clearly for later reference

---

## 📊 Understanding Results

### Confidence Scores
- **0.0 - 0.3**: Low confidence (uncertain)
- **0.3 - 0.7**: Medium confidence (moderate)
- **0.7 - 1.0**: High confidence (certain)

### Analysis Results
Different models return different results:
- **ResNet50**: Top-5 class predictions
- **CLIP**: Embedding vector
- **YOLOv8**: Detected objects and boxes

### Drill Reproducibility
- Same seed = exact same images
- Different seeds = different images
- Useful for testing and benchmarking

---

## 🔐 Best Practices

1. **API Keys**:
   - Never commit keys to git
   - Use environment variables
   - Rotate keys regularly

2. **Database**:
   - Back up `data/red_marker.db` regularly
   - Don't delete it unless resetting
   - Check size periodically

3. **Models**:
   - Only load models you need
   - Monitor disk space for models
   - Use lightweight models for testing

4. **Generation**:
   - Set reasonable intervals (5+ seconds)
   - Use max_images to avoid storage issues
   - Monitor generation progress

5. **Security**:
   - Don't expose API without authentication
   - Use HTTPS in production
   - Validate all user inputs

---

## 🚀 Next Steps

1. **Explore Features**: Try each tab to understand capabilities
2. **Create Drills**: Save reproducible configurations
3. **Analyze Results**: Compare different models
4. **Integrate**: Use API in your own applications
5. **Customize**: Modify models and prompts

---

## 📞 Getting Help

**Check These Resources**:
1. `README_PRO.md` - Full feature documentation
2. `IMPLEMENTATION_SUMMARY.md` - Technical details
3. API Docs - http://localhost:5000/docs
4. Browser Console - F12 for error messages

**Common Commands**:
```bash
# Start server
python run.py

# Activate venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Reset database
rm -rf data/red_marker.db

# View logs
tail -f logs/app.log
```

---

## ✨ Key Features Summary

| Feature | Status | How To |
|---------|--------|-------|
| Image Annotation | ✅ | Upload → Click → Mark |
| Continuous Generation | ✅ | Enter prompts → Start |
| Deterministic Drills | ✅ | Name + Seed + Create |
| Navigation | ✅ | Previous/Next/GoTo |
| Vision Analysis | ✅ | Image ID → Analyze |
| Model Switching | ✅ | Select → Update |
| Database Storage | ✅ | Automatic |
| Pagination | ✅ | Page controls |
| History Tracking | ✅ | Auto-tracked |
| Reset Function | ✅ | Click Reset button |

---

## 🎯 Success Criteria

You'll know everything is working when:
- ✅ Can upload and annotate images
- ✅ Can generate images continuously
- ✅ Can create reproducible drills
- ✅ Can navigate through images
- ✅ Can analyze with vision models
- ✅ Can switch models without restart
- ✅ Can see results in database

---

**Version**: 2.0.0  
**Status**: Ready to Use  
**Last Updated**: May 17, 2024

Enjoy Red Marker Pro! 🎉
