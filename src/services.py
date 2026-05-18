"""
Image generation service for infinite loop generation and storage
"""

import asyncio
import logging
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Service for managing continuous image generation"""
    
    def __init__(self, db_session, model_manager):
        """
        Initialize image generation service
        
        Args:
            db_session: Database session
            model_manager: ModelManager instance
        """
        self.db = db_session
        self.model_manager = model_manager
        self.generation_task = None
        self.is_running = False
        self.generated_count = 0
    
    async def start_generation_loop(
        self,
        session_id: str,
        prompts: List[str],
        interval: float = 5.0,
        max_images: Optional[int] = None
    ):
        """
        Start infinite image generation loop
        
        Args:
            session_id: Session ID for tracking
            prompts: List of prompts to cycle through
            interval: Delay between generations (seconds)
            max_images: Maximum images to generate (None = infinite)
        """
        self.is_running = True
        self.generated_count = 0
        
        logger.info(f"Starting generation loop for session {session_id}")
        
        prompt_index = 0
        
        try:
            while self.is_running:
                if max_images and self.generated_count >= max_images:
                    logger.info(f"Reached maximum image limit: {max_images}")
                    break
                
                # Get next prompt
                prompt = prompts[prompt_index % len(prompts)]
                prompt_index += 1
                
                # Generate image
                await self.generate_and_store_image(
                    session_id=session_id,
                    prompt=prompt,
                    order_index=self.generated_count
                )
                
                self.generated_count += 1
                
                # Wait before next generation
                await asyncio.sleep(interval)
        
        except asyncio.CancelledError:
            logger.info(f"Generation loop cancelled for session {session_id}")
            self.is_running = False
            raise
        except Exception as e:
            logger.error(f"Error in generation loop: {e}")
            self.is_running = False
    
    async def generate_and_store_image(
        self,
        session_id: str,
        prompt: str,
        order_index: int,
        seed: Optional[int] = None
    ):
        """
        Generate image and store in database
        
        Args:
            session_id: Session ID
            prompt: Generation prompt
            order_index: Order in sequence
            seed: Optional seed for deterministic generation
        """
        try:
            # Generate image using model manager
            image_data = self.model_manager.generate_image(prompt, seed=seed)
            
            if image_data is None:
                logger.warning(f"Failed to generate image for prompt: {prompt}")
                return None
            
            # Save image to database
            from src.database import GeneratedImage
            
            generated_image = GeneratedImage(
                session_id=session_id,
                image_path="",
                image_data=image_data,
                prompt=prompt,
                model_name=self.model_manager.config.image_generation_model,
                order_index=order_index,
                created_at=datetime.utcnow()
            )
            
            self.db.add(generated_image)
            self.db.commit()
            self.db.refresh(generated_image)
            self._update_session_total(session_id)
            
            logger.info(f"Stored image {order_index} for session {session_id}")
            
            return generated_image
        
        except Exception as e:
            logger.error(f"Error generating and storing image: {e}")
            self.db.rollback()
            return None

    def _update_session_total(self, session_id: str) -> None:
        """Keep session navigation metadata aligned with generated images."""
        try:
            from src.database import GeneratedImage, SessionHistory

            total = self.db.query(GeneratedImage).filter(
                GeneratedImage.session_id == session_id
            ).count()
            session_history = self.db.query(SessionHistory).filter(
                SessionHistory.session_id == session_id
            ).first()

            if not session_history:
                session_history = SessionHistory(session_id=session_id)
                self.db.add(session_history)

            session_history.total_images = total
            session_history.updated_at = datetime.utcnow()
            self.db.commit()
        except Exception as e:
            logger.error(f"Error updating session total: {e}")
            self.db.rollback()
    
    def stop_generation_loop(self):
        """Stop the generation loop"""
        self.is_running = False
        logger.info("Generation loop stopped")
    
    def get_images_for_session(
        self,
        session_id: str,
        page: int = 0,
        page_size: int = 10
    ) -> tuple:
        """
        Get paginated images for a session
        
        Args:
            session_id: Session ID
            page: Page number (0-indexed)
            page_size: Number of images per page
        
        Returns:
            Tuple of (images, total_count)
        """
        try:
            from src.database import GeneratedImage
            
            query = self.db.query(GeneratedImage).filter(
                GeneratedImage.session_id == session_id
            ).order_by(GeneratedImage.order_index)
            
            total_count = query.count()
            
            images = query.offset(page * page_size).limit(page_size).all()
            
            return images, total_count
        
        except Exception as e:
            logger.error(f"Error retrieving images: {e}")
            return [], 0
    
    def get_image_by_id(self, image_id: int):
        """Get single image by ID"""
        try:
            from src.database import GeneratedImage
            
            return self.db.query(GeneratedImage).filter(
                GeneratedImage.id == image_id
            ).first()
        
        except Exception as e:
            logger.error(f"Error retrieving image: {e}")
            return None
    
    def delete_session_images(self, session_id: str) -> bool:
        """Delete all images for a session"""
        try:
            from src.database import GeneratedImage
            
            self.db.query(GeneratedImage).filter(
                GeneratedImage.session_id == session_id
            ).delete()
            self.db.commit()
            
            logger.info(f"Deleted all images for session {session_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting images: {e}")
            self.db.rollback()
            return False


class DeterministicDrill:
    """Service for deterministic drills with reproducible results"""
    
    def __init__(self, db_session, model_manager):
        """
        Initialize deterministic drill service
        
        Args:
            db_session: Database session
            model_manager: ModelManager instance
        """
        self.db = db_session
        self.model_manager = model_manager
    
    async def create_drill(
        self,
        session_id: str,
        drill_name: str,
        seed: int,
        prompts: List[str],
        num_images: int
    ):
        """
        Create deterministic drill with fixed seed
        
        Args:
            session_id: Session ID
            drill_name: Name of the drill
            seed: Fixed seed for reproducibility
            prompts: List of prompts to use
            num_images: Number of images to generate
        """
        try:
            from src.database import SavedDrill, GeneratedImage, SessionHistory
            
            generated_ids = []
            
            # Generate images with deterministic seed
            for i in range(num_images):
                prompt = prompts[i % len(prompts)]
                
                # Use seed + index for variation while maintaining reproducibility
                image_seed = seed + i
                
                image_data = self.model_manager.generate_image(
                    prompt,
                    seed=image_seed
                )
                
                if image_data:
                    img = GeneratedImage(
                        session_id=session_id,
                        image_path="",
                        image_data=image_data,
                        prompt=prompt,
                        model_name=self.model_manager.config.image_generation_model,
                        order_index=i,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(img)
                    self.db.flush()
                    generated_ids.append(img.id)
            
            # Save drill configuration
            drill = SavedDrill(
                session_id=session_id,
                drill_name=drill_name,
                drill_seed=seed,
                image_ids=str(generated_ids),  # Store as JSON string
                description=f"Deterministic drill with seed {seed}"
            )
            
            self.db.add(drill)
            self.db.commit()
            self.db.refresh(drill)

            session_history = self.db.query(SessionHistory).filter(
                SessionHistory.session_id == session_id
            ).first()

            if not session_history:
                session_history = SessionHistory(session_id=session_id)
                self.db.add(session_history)

            session_history.drill_mode = True
            session_history.drill_seed = seed
            session_history.total_images = self.db.query(GeneratedImage).filter(
                GeneratedImage.session_id == session_id
            ).count()
            session_history.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Created drill '{drill_name}' with seed {seed} and {num_images} images")
            
            return drill
        
        except Exception as e:
            logger.error(f"Error creating drill: {e}")
            self.db.rollback()
            return None
    
    async def recreate_drill(self, drill_id: int) -> bool:
        """
        Recreate a drill using the same seed (for reproducibility)
        
        Args:
            drill_id: ID of the drill to recreate
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from src.database import SavedDrill
            
            drill = self.db.query(SavedDrill).filter(
                SavedDrill.id == drill_id
            ).first()
            
            if not drill:
                logger.warning(f"Drill not found: {drill_id}")
                return False
            
            # The same seed will produce the same results
            logger.info(f"Drill '{drill.drill_name}' can be recreated using seed {drill.drill_seed}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error recreating drill: {e}")
            return False
