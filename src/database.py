"""
Database configuration and session management for Red Marker application
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, LargeBinary, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from src.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Database Models
class GeneratedImage(Base):
    """Model for storing generated images"""
    __tablename__ = "generated_images"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True)
    image_path = Column(String(255), nullable=False)
    image_data = Column(LargeBinary, nullable=True)  # Store image binary data
    prompt = Column(Text, nullable=True)
    model_name = Column(String(100), default="gemini-pro-vision")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    order_index = Column(Integer, index=True)  # For pagination
    
    # Relationships
    vision_analyses = relationship("VisionAnalysis", back_populates="image")


class VisionAnalysis(Base):
    """Model for vision model analysis results"""
    __tablename__ = "vision_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("generated_images.id"))
    model_name = Column(String(100), default="local-vision-model")
    analysis_result = Column(Text, nullable=True)  # JSON or text description
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    image = relationship("GeneratedImage", back_populates="vision_analyses")


class SessionHistory(Base):
    """Model for tracking user session history"""
    __tablename__ = "session_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True, unique=True)
    user_id = Column(String(100), nullable=True)
    current_image_index = Column(Integer, default=0)
    total_images = Column(Integer, default=0)
    drill_mode = Column(Boolean, default=False)
    drill_seed = Column(Integer, nullable=True)  # For deterministic drill
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    saved_drills = relationship("SavedDrill", back_populates="session")


class SavedDrill(Base):
    """Model for storing drill configurations and results"""
    __tablename__ = "saved_drills"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("session_history.session_id"))
    drill_name = Column(String(255))
    drill_seed = Column(Integer)  # Seed for reproducibility
    image_ids = Column(Text)  # JSON array of image IDs
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("SessionHistory", back_populates="saved_drills")


class MarkerAnnotation(Base):
    """Model for storing marker annotations"""
    __tablename__ = "marker_annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True)
    image_id = Column(Integer, ForeignKey("generated_images.id"), nullable=True)
    x = Column(Integer)
    y = Column(Integer)
    marker_type = Column(String(50), default="red")
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
