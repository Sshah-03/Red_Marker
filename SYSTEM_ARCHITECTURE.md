# Red Marker Pro v2.0.0 - System Architecture

## 🏗️ OVERALL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE (Browser)                       │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐          │
│  │   Upload &   │      AI      │   History &  │    Vision    │  Model  │
│  │  Annotate    │  Generation  │ Navigation   │   Analysis   │  Config │
│  └──────────────┴──────────────┴──────────────┴──────────────┴──────────┘
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND SERVER                             │
│                         (localhost:5000)                                │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                   ROUTE HANDLERS (20+ endpoints)              │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │    │
│  │  │ Generation   │ │ Analysis     │ │ Navigation   │ ...       │    │
│  │  │ /generate/*  │ │ /analyze/*   │ │ /session/*   │           │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘           │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                    ▼                                    │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                   SERVICE LAYER (Business Logic)              │    │
│  │  ┌──────────────────┐ ┌──────────────────────────────────┐   │    │
│  │  │ImageGeneration   │ │VisionAnalysis     DeterministicDrill│   │    │
│  │  │Service           │ │Service                         │   │    │
│  │  │ • Generate loop  │ │ • Analyze image              │   │    │
│  │  │ • Store results  │ │ • Batch process              │   │    │
│  │  │ • Get paginated  │ │ • Compare results            │   │    │
│  │  │   images         │ │ • Score extraction           │   │    │
│  │  └──────────────────┘ └──────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                    ▼                                    │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                   MODEL LAYER (AI Models)                      │    │
│  │  ┌──────────────────────┐  ┌──────────────────────────────┐   │    │
│  │  │ImageGenerationModel  │  │VisionModel (Multi-backend)   │   │    │
│  │  │(Gemini API Wrapper)  │  │                              │   │    │
│  │  │ • Gemini 1.5 Pro     │  │ • ResNet50                   │   │    │
│  │  │ • Gemini 1.0 Vision  │  │ • CLIP                       │   │    │
│  │  │ • Custom via API     │  │ • YOLOv8                     │   │    │
│  │  │                      │  │ • Custom (user-defined)      │   │    │
│  │  └──────────────────────┘  └──────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                    ▼                                    │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                   DATA LAYER (SQLAlchemy ORM)                 │    │
│  │  Models: GeneratedImage, VisionAnalysis, SessionHistory,      │    │
│  │          SavedDrill, MarkerAnnotation                         │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER (SQLite)                            │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  GeneratedImage | VisionAnalysis | SessionHistory | SavedDrill│    │
│  │  MarkerAnnotation                                              │    │
│  │                                                                │    │
│  │  File: data/red_marker.db                                      │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                                  │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐    │
│  │   Google Generative AI       │  │   PyTorch / OpenCV / YOLOv8  │    │
│  │   (Gemini Image Generation)  │  │   (Local Vision Models)      │    │
│  └──────────────────────────────┘  └──────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```


## 📡 DATA FLOW

### Image Generation Flow
```
User Input (Prompts)
        ▼
Start Generation Button
        ▼
FastAPI /api/generate/start
        ▼
ImageGenerationService.start_generation_loop()
        ▼
Loop: For each prompt
  ├─ Gemini API calls
  ├─ Image generation
  ├─ generate_and_store_image()
  └─ Save to database
        ▼
User browses: GET /api/generated-images/{session}
        ▼
Frontend displays with pagination
```

### Vision Analysis Flow
```
User Input (Image ID)
        ▼
Select Model (ResNet50, CLIP, YOLOv8)
        ▼
FastAPI /api/analyze/image
        ▼
VisionAnalysisService.analyze_image()
        ▼
Load model from ModelManager
        ▼
Analyze image binary from database
        ▼
Extract confidence scores
        ▼
Store results in VisionAnalysis table
        ▼
Return to frontend
        ▼
Display results with confidence
```

### Navigation Flow
```
User selects image or clicks Previous/Next
        ▼
FastAPI /api/session/{session}/navigate
        ▼
SessionHistory model updated
        ▼
Navigation history recorded
        ▼
Return image data
        ▼
Frontend displays image
```

### Deterministic Drill Flow
```
User Input (Name, Seed, Count)
        ▼
Create Drill Button
        ▼
FastAPI /api/drill/create
        ▼
DeterministicDrill.create_drill()
        ▼
Generate images with same seed
        ▼
Store images AND drill metadata
        ▼
Save to SavedDrill table
        ▼
User can later click "Recreate"
        ▼
DeterministicDrill.recreate_drill()
        ▼
Same seed generates exact same images
```


## 🔌 API ARCHITECTURE

### Request/Response Pattern
```
┌─────────────────┐
│   Browser/User  │
└────────┬────────┘
         │
         │ HTTP Request
         ▼
┌──────────────────────────────┐
│  FastAPI Endpoint Handler    │
│  (Validation, Routing)       │
└──────────┬───────────────────┘
           │
           │ Call
           ▼
┌──────────────────────────────┐
│  Business Logic Service      │
│  (ImageGeneration, Vision)   │
└──────────┬───────────────────┘
           │
           │ Query/Update
           ▼
┌──────────────────────────────┐
│  Database (SQLAlchemy ORM)   │
│  Models & Relationships      │
└──────────┬───────────────────┘
           │
           │ SQL Query
           ▼
┌──────────────────────────────┐
│  SQLite Database             │
│  (data/red_marker.db)        │
└──────────┬───────────────────┘
           │
           │ Result Set
           ▼
┌──────────────────────────────┐
│  Service Layer Processing    │
└──────────┬───────────────────┘
           │
           │ JSON Response
           ▼
┌──────────────────────────────┐
│  FastAPI Response Model      │
│  (Pydantic Validation)       │
└──────────┬───────────────────┘
           │
           │ HTTP Response
           ▼
┌─────────────────┐
│   Browser/User  │
└─────────────────┘
```


## 📂 FILE ORGANIZATION

```
Red_marker/
├── Backend (src/)
│   ├── database.py              ← ORM models (5 tables)
│   ├── model_loader.py          ← Model management
│   ├── services.py              ← Generation & drill logic
│   ├── vision_service.py        ← Vision analysis
│   ├── api/
│   │   ├── routes.py            ← Original endpoints
│   │   └── routes_enhanced.py   ← New 20+ endpoints
│   ├── config.py                ← Settings
│   ├── main.py                  ← App setup
│   └── models.py                ← Response schemas
│
├── Frontend (static/)
│   ├── index.html               ← 5-tab UI
│   ├── js/
│   │   ├── script.js            ← Core logic
│   │   ├── generation.js        ← Generation UI
│   │   ├── history.js           ← Navigation UI
│   │   ├── analysis.js          ← Analysis UI
│   │   └── models.js            ← Config UI
│   └── css/
│       └── style.css            ← Styling
│
├── Database
│   └── data/red_marker.db       ← SQLite database (auto-created)
│
├── Configuration
│   ├── app.py                   ← Flask/FastAPI entry
│   ├── run.py                   ← Application runner
│   ├── requirements.txt         ← Dependencies
│   ├── .env.example             ← Config template
│   ├── setup.sh                 ← Setup script
│   └── quickstart.py            ← Auto-start
│
└── Documentation
    ├── README.md                ← Original README
    ├── README_PRO.md            ← Feature guide
    ├── GETTING_STARTED.md       ← Quick start
    ├── IMPLEMENTATION_SUMMARY.md← Technical
    ├── QUICK_REFERENCE.md       ← Quick help
    ├── PROJECT_STRUCTURE.txt    ← File org
    ├── IMPLEMENTATION_CHECKLIST ← Feature list
    ├── COMPLETION_SUMMARY.md    ← Overview
    ├── FINAL_SUMMARY.txt        ← This project
    └── DOCUMENTATION_INDEX.md   ← Doc map
```


## 🗄️ DATABASE RELATIONSHIPS

```
GeneratedImage (PK: id)
├── image_binary (BLOB)
├── prompt (TEXT)
├── model_name (TEXT)
├── order_index (INT)
├── session_id (FK)
└── created_at (TIMESTAMP)
    │
    ├──→ VisionAnalysis (1:N)
    │    ├── model_name
    │    ├── results (JSON)
    │    ├── confidence (FLOAT)
    │    └── created_at
    │
    ├──→ MarkerAnnotation (1:N)
    │    ├── x_coordinate
    │    ├── y_coordinate
    │    └── created_at
    │
    └──→ SessionHistory
         ├── current_image_index
         ├── drill_mode
         ├── current_seed
         └── created_at
              │
              └──→ SavedDrill (1:N)
                   ├── drill_name
                   ├── seed
                   ├── num_images
                   └── created_at
```


## 🚀 DEPLOYMENT FLOW

```
Local Development:
  python run.py
        ▼
  http://localhost:5000
        ▼
  Development mode (SQLite)

Production:
  python run.py (environment: production)
        ▼
  PostgreSQL database (via DATABASE_URL)
        ▼
  https://yourdomain.com
        ▼
  Gunicorn/ASGI server
```


## 🔄 REQUEST LIFECYCLE

```
1. User Action (Click button)
   └─ JavaScript event handler triggered
   
2. Frontend Processing
   └─ Validate input
   └─ Prepare request data
   └─ Show loading indicator
   
3. HTTP Request
   └─ POST/GET to /api/endpoint
   └─ Include headers, auth, body
   
4. Backend Routing
   └─ FastAPI matches route
   └─ Validate with Pydantic
   
5. Business Logic
   └─ Service layer processes
   └─ May call external APIs (Gemini, PyTorch)
   
6. Database Operations
   └─ SQLAlchemy ORM queries
   └─ Execute SQL on SQLite/PostgreSQL
   
7. Response Preparation
   └─ Format response with Pydantic
   └─ Convert to JSON
   
8. HTTP Response
   └─ Status code + headers + body
   
9. Frontend Handling
   └─ Parse JSON response
   └─ Update DOM
   └─ Hide loading indicator
   
10. User Sees Result
    └─ Image displayed
    └─ Message shown
    └─ UI updated
```


## ⚡ PERFORMANCE ARCHITECTURE

```
Optimization Strategies:
├── Database
│   ├─ Indices on frequently queried columns
│   ├─ Pagination to limit result sets
│   └─ Connection pooling
│
├── Backend
│   ├─ Async/await for long operations
│   ├─ Background tasks for generation
│   └─ Caching of model instances
│
├── Frontend
│   ├─ Lazy loading of images
│   ├─ Pagination of results
│   ├─ Efficient DOM manipulation
│   └─ CSS optimization
│
└── External
    ├─ Model loading once at startup
    ├─ Batch processing support
    └─ Concurrent requests possible
```


## 🔐 SECURITY ARCHITECTURE

```
Authentication:
├─ API Key in environment variable
├─ Not exposed in frontend
├─ Securely passed to Gemini

Input Validation:
├─ Pydantic models validate all inputs
├─ File size limits
├─ Prompt sanitization

Database:
├─ SQLAlchemy prevents SQL injection
├─ Parameterized queries
├─ No direct SQL string formatting

API:
├─ CORS configured appropriately
├─ Error messages don't expose internals
├─ Rate limiting possible (add-on)
```


## 📊 SCALABILITY PATH

```
Current (Development):
  SQLite → Single process → Local models → 100s of images

Scale To (Small Production):
  PostgreSQL → Gunicorn 4 workers → Local models → 1000s of images

Scale To (Medium Production):
  PostgreSQL → 8+ workers → Model server → 10000s of images

Scale To (Large Production):
  PostgreSQL cluster → Load balancer → GPU server → 100000s of images
  Redis caching → Task queue (Celery) → Model serving (TorchServe)
```


## 🎯 COMPONENT RELATIONSHIPS

```
User Interface
    ↓
FastAPI Endpoints
    ↓ ┌─────────────────┬─────────────────┬──────────────┐
    │ │                 │                 │              │
ImageGenService  VisionService  DrillService  HistoryService
    │ │                 │                 │              │
    └─┴─────────────────┴─────────────────┴──────────────┘
                        ↓
                  ModelManager
    ↓           (ImageGenModel, VisionModel)
    │                   ↓
    ├───────→ External APIs & Models
    │        (Gemini, PyTorch, CLIP, YOLOv8)
    │
    ↓
SQLAlchemy ORM
    ↓
SQLite Database (or PostgreSQL)
```


---

This architecture provides:
✅ Clean separation of concerns
✅ Scalability from development to production
✅ Multiple model support
✅ Persistence of all data
✅ REST API for external integration
✅ Responsive user interface
✅ Background task support
✅ Error handling throughout
