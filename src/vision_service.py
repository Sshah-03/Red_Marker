"""
Vision model analysis service
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class VisionAnalysisService:
    """Service for analyzing images with vision models"""
    
    def __init__(self, db_session, model_manager):
        """
        Initialize vision analysis service
        
        Args:
            db_session: Database session
            model_manager: ModelManager instance
        """
        self.db = db_session
        self.model_manager = model_manager
    
    def analyze_image(
        self,
        image_id: int,
        image_data: bytes
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze image using configured vision model
        
        Args:
            image_id: ID of the image in database
            image_data: Binary image data
        
        Returns:
            Analysis results or None if failed
        """
        try:
            from src.database import VisionAnalysis
            
            # Run analysis
            analysis_result = self.model_manager.analyze_image(image_data)
            
            # Extract confidence score if available
            confidence_score = None
            if isinstance(analysis_result, dict):
                # Try to extract confidence from various model types
                if "confidence_scores" in analysis_result:
                    confidence_score = analysis_result["confidence_scores"][0] if analysis_result["confidence_scores"] else None
                elif "detection_count" in analysis_result:
                    confidence_score = 1.0 if analysis_result["detection_count"] > 0 else 0.0
            
            # Store analysis in database
            created_at = datetime.utcnow()
            model_name = self.model_manager.config.vision_model
            if isinstance(analysis_result, dict) and analysis_result.get("model"):
                model_name = analysis_result["model"]

            analysis = VisionAnalysis(
                image_id=image_id,
                model_name=model_name,
                analysis_result=json.dumps(analysis_result),
                confidence_score=confidence_score,
                created_at=created_at
            )
            
            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
            
            logger.info(f"Analyzed image {image_id} with model {self.model_manager.config.vision_model}")
            
            return {
                "id": analysis.id,
                "image_id": image_id,
                "model": analysis.model_name,
                "results": analysis_result,
                "confidence": confidence_score,
                "created_at": analysis.created_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            self.db.rollback()
            return None
    
    def batch_analyze_images(
        self,
        image_ids: list,
        get_image_data_fn
    ) -> Dict[int, Dict[str, Any]]:
        """
        Analyze multiple images
        
        Args:
            image_ids: List of image IDs to analyze
            get_image_data_fn: Function to retrieve image data by ID
        
        Returns:
            Dictionary mapping image_id to analysis results
        """
        results = {}
        
        for image_id in image_ids:
            try:
                image_data = get_image_data_fn(image_id)
                if image_data:
                    result = self.analyze_image(image_id, image_data)
                    if result:
                        results[image_id] = result
            except Exception as e:
                logger.error(f"Error analyzing image {image_id}: {e}")
                continue
        
        logger.info(f"Batch analyzed {len(results)} images")
        return results
    
    def get_analysis_for_image(self, image_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored analysis for an image
        
        Args:
            image_id: ID of the image
        
        Returns:
            Analysis data or None if not found
        """
        try:
            from src.database import VisionAnalysis
            
            analysis = self.db.query(VisionAnalysis).filter(
                VisionAnalysis.image_id == image_id
            ).order_by(VisionAnalysis.created_at.desc()).first()
            
            if not analysis:
                return None
            
            return {
                "id": analysis.id,
                "image_id": analysis.image_id,
                "model": analysis.model_name,
                "results": self._parse_analysis_result(analysis.analysis_result),
                "confidence": analysis.confidence_score,
                "created_at": analysis.created_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error retrieving analysis: {e}")
            return None
    
    def get_latest_analyses(
        self,
        session_id: str,
        limit: int = 10
    ) -> list:
        """
        Get latest analyses for a session
        
        Args:
            session_id: Session ID
            limit: Maximum number of results
        
        Returns:
            List of analysis results
        """
        try:
            from src.database import VisionAnalysis, GeneratedImage
            
            analyses = self.db.query(VisionAnalysis).join(
                GeneratedImage
            ).filter(
                GeneratedImage.session_id == session_id
            ).order_by(VisionAnalysis.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": a.id,
                    "image_id": a.image_id,
                    "model": a.model_name,
                    "results": self._parse_analysis_result(a.analysis_result),
                    "confidence": a.confidence_score,
                    "created_at": a.created_at.isoformat()
                }
                for a in analyses
            ]
        
        except Exception as e:
            logger.error(f"Error retrieving analyses: {e}")
            return []
    
    def compare_analyses(
        self,
        image_id1: int,
        image_id2: int
    ) -> Dict[str, Any]:
        """
        Compare analyses of two images
        
        Args:
            image_id1: First image ID
            image_id2: Second image ID
        
        Returns:
            Comparison results
        """
        try:
            analysis1 = self.get_analysis_for_image(image_id1)
            analysis2 = self.get_analysis_for_image(image_id2)
            
            if not analysis1 or not analysis2:
                return {"error": "One or both images not analyzed"}
            
            return {
                "image1": analysis1,
                "image2": analysis2,
                "confidence_diff": abs(
                    (analysis1.get("confidence") or 0) - 
                    (analysis2.get("confidence") or 0)
                )
            }
        
        except Exception as e:
            logger.error(f"Error comparing analyses: {e}")
            return {"error": str(e)}

    @staticmethod
    def _parse_analysis_result(raw_result: Optional[str]) -> Any:
        if raw_result is None:
            return None
        try:
            return json.loads(raw_result)
        except (TypeError, json.JSONDecodeError):
            return raw_result
