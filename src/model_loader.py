"""
Configurable model loader for image generation and vision analysis
Allows flexible switching between different models
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging
import hashlib
import io
import random

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for models"""
    image_generation_model: str = "gemini-1.5-pro"  # Gemini model for image generation
    vision_model: str = "resnet50"  # Local vision model (can be changed to any local model)
    vision_model_path: Optional[str] = None  # Path to local model weights if needed
    image_generation_api_key: Optional[str] = None  # Gemini API key
    image_size: tuple = (512, 512)  # Default image generation size
    max_retries: int = 3
    timeout: int = 60


class ImageGenerationModel:
    """Wrapper for image generation model (Gemini)"""
    
    def __init__(self, config: ModelConfig):
        """
        Initialize image generation model
        
        Args:
            config: ModelConfig instance with model settings
        """
        self.config = config
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Gemini model"""
        try:
            import google.genai as genai
            
            api_key = self.config.image_generation_api_key or os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not found. Image generation will not work.")
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.config.image_generation_model)
            logger.info(f"Initialized image generation model: {self.config.image_generation_model}")
        except Exception as e:
            logger.error(f"Failed to initialize image generation model: {e}")
            self.model = None
    
    def generate_image(self, prompt: str, seed: Optional[int] = None) -> Optional[bytes]:
        """
        Generate image using Gemini API
        
        Args:
            prompt: Text prompt for image generation
            seed: Seed for deterministic generation (if supported)
        
        Returns:
            Image bytes or None if generation fails
        """
        if not self.model:
            logger.warning("Image generation model not initialized; using local fallback image")
            return self._generate_fallback_image(prompt, seed)
        
        try:
            # Gemini doesn't support direct seed parameter, so we use seed in prompt for determinism
            if seed is not None:
                prompt_with_seed = f"{prompt} [seed:{seed}]"
            else:
                prompt_with_seed = prompt
            
            response = self.model.generate_content(prompt_with_seed)
            
            if getattr(response, "parts", None):
                for part in response.parts:
                    if hasattr(part, 'data'):
                        return part.data
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data and getattr(inline_data, "data", None):
                        return inline_data.data
            
            logger.warning(f"No image data in response for prompt: {prompt}")
            return self._generate_fallback_image(prompt, seed)
        
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return self._generate_fallback_image(prompt, seed)

    def _generate_fallback_image(self, prompt: str, seed: Optional[int] = None) -> bytes:
        """Create a deterministic placeholder image when external generation is unavailable."""
        from PIL import Image, ImageDraw, ImageFont

        seed_material = f"{prompt}:{seed if seed is not None else ''}".encode("utf-8")
        digest = hashlib.sha256(seed_material).digest()
        rng = random.Random(int.from_bytes(digest[:8], "big"))

        width, height = self.config.image_size
        base = tuple(40 + rng.randint(0, 120) for _ in range(3))
        accent = tuple(100 + rng.randint(0, 155) for _ in range(3))
        image = Image.new("RGB", (width, height), base)
        draw = ImageDraw.Draw(image, "RGBA")

        for _ in range(18):
            x0 = rng.randint(-width // 4, width)
            y0 = rng.randint(-height // 4, height)
            size = rng.randint(width // 8, width // 2)
            color = (*accent, rng.randint(28, 90))
            draw.ellipse((x0, y0, x0 + size, y0 + size), fill=color)

        wrapped = self._wrap_text(prompt or "Generated image", 30)[:6]
        try:
            font = ImageFont.truetype("Arial.ttf", 22)
        except Exception:
            font = ImageFont.load_default()

        panel_height = 42 + len(wrapped) * 25
        draw.rectangle((24, height - panel_height - 24, width - 24, height - 24), fill=(0, 0, 0, 135))
        y = height - panel_height - 8
        for line in wrapped:
            draw.text((42, y), line, fill=(255, 255, 255, 235), font=font)
            y += 25

        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

    @staticmethod
    def _wrap_text(text: str, width: int) -> list:
        words = text.split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word[:width]
        if current:
            lines.append(current)
        return lines or ["Generated image"]
    
    def set_model(self, model_name: str):
        """Change the image generation model"""
        self.config.image_generation_model = model_name
        self._initialize_model()


class VisionModel:
    """Wrapper for local vision model"""
    
    def __init__(self, config: ModelConfig):
        """
        Initialize vision model
        
        Args:
            config: ModelConfig instance with model settings
        """
        self.config = config
        self.model = None
        self.processor = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize vision model (supports multiple backends)"""
        self.model = None
        self.processor = None
        try:
            if self.config.vision_model == "resnet50":
                self._init_resnet50()
            elif self.config.vision_model == "clip":
                self._init_clip()
            elif self.config.vision_model == "yolo":
                self._init_yolo()
            elif self.config.vision_model == "custom":
                self._init_custom_model()
            else:
                logger.warning(f"Unknown vision model: {self.config.vision_model}")
        except Exception as e:
            logger.error(f"Failed to initialize vision model: {e}")
            self.model = None
    
    def _init_resnet50(self):
        """Initialize ResNet50 for image classification"""
        try:
            import torchvision.models as models
            import torch
            
            self.model = models.resnet50(pretrained=True)
            self.model.eval()
            logger.info("Initialized ResNet50 vision model")
        except ImportError:
            logger.error("PyTorch/torchvision not installed. Install with: pip install torch torchvision")
    
    def _init_clip(self):
        """Initialize CLIP model for vision-language tasks"""
        try:
            import clip
            
            self.model, self.processor = clip.load("ViT-B/32")
            self.model.eval()
            logger.info("Initialized CLIP vision model")
        except ImportError:
            logger.error("OpenAI CLIP not installed. Install with: pip install openai-clip")
    
    def _init_yolo(self):
        """Initialize YOLO for object detection"""
        try:
            from ultralytics import YOLO
            
            self.model = YOLO("yolov8n.pt")
            logger.info("Initialized YOLOv8 vision model")
        except ImportError:
            logger.error("YOLOv8 not installed. Install with: pip install ultralytics")
    
    def _init_custom_model(self):
        """Initialize custom model from path"""
        try:
            if self.config.vision_model_path:
                # Load custom model from path
                logger.info(f"Loading custom model from: {self.config.vision_model_path}")
                # Implementation depends on custom model format
            else:
                logger.error("Custom model path not specified")
        except Exception as e:
            logger.error(f"Failed to load custom model: {e}")
    
    def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze image using vision model
        
        Args:
            image_data: Image bytes to analyze
        
        Returns:
            Dictionary with analysis results
        """
        if not self.model:
            logger.warning("Vision model not initialized; using basic local image analysis")
            return self._analyze_basic(image_data)
        
        try:
            if self.config.vision_model == "resnet50":
                return self._analyze_resnet50(image_data)
            elif self.config.vision_model == "clip":
                return self._analyze_clip(image_data)
            elif self.config.vision_model == "yolo":
                return self._analyze_yolo(image_data)
            else:
                return self._analyze_basic(image_data)
        
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {"error": str(e)}
    
    def _analyze_resnet50(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze image with ResNet50"""
        try:
            from PIL import Image
            import torch
            import torchvision.transforms as transforms
            import io
            
            # Load and preprocess image
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            preprocess = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            
            input_tensor = preprocess(image).unsqueeze(0)
            
            with torch.no_grad():
                output = self.model(input_tensor)
            
            return {
                "model": "resnet50",
                "output_shape": list(output.shape),
                "confidence_scores": output.softmax(1)[0].topk(5).values.tolist(),
                "status": "success"
            }
        except Exception as e:
            return {"error": f"ResNet50 analysis failed: {e}"}
    
    def _analyze_clip(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze image with CLIP"""
        try:
            import torch
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            image_input = self.processor(image).unsqueeze(0)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
            
            return {
                "model": "clip",
                "embedding_shape": list(image_features.shape),
                "status": "success"
            }
        except Exception as e:
            return {"error": f"CLIP analysis failed: {e}"}
    
    def _analyze_yolo(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze image with YOLO"""
        try:
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            results = self.model(image)
            
            detections = []
            for result in results:
                for box in result.boxes:
                    detections.append({
                        "class": int(box.cls),
                        "confidence": float(box.conf),
                        "bbox": box.xyxy.tolist()
                    })
            
            return {
                "model": "yolo",
                "detections": detections,
                "detection_count": len(detections),
                "status": "success"
            }
        except Exception as e:
            return {"error": f"YOLO analysis failed: {e}"}

    def _analyze_basic(self, image_data: bytes) -> Dict[str, Any]:
        """Dependency-free image analysis used when optional ML models are unavailable."""
        try:
            from PIL import Image, ImageStat

            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            stat = ImageStat.Stat(image)
            means = stat.mean
            brightness = sum(means) / (3 * 255)
            dominant_channel = ["red", "green", "blue"][max(range(3), key=lambda i: means[i])]

            return {
                "model": "basic",
                "width": image.width,
                "height": image.height,
                "average_rgb": [round(value, 2) for value in means],
                "brightness": round(brightness, 4),
                "dominant_channel": dominant_channel,
                "confidence_scores": [round(brightness, 4)],
                "status": "success"
            }
        except Exception as e:
            return {"error": f"Basic analysis failed: {e}"}
    
    def set_model(self, model_name: str, model_path: Optional[str] = None):
        """Change the vision model"""
        self.config.vision_model = model_name
        if model_path:
            self.config.vision_model_path = model_path
        self._initialize_model()


class ModelManager:
    """Central manager for all models"""
    
    def __init__(self, config: Optional[ModelConfig] = None):
        """
        Initialize model manager
        
        Args:
            config: ModelConfig instance (creates default if None)
        """
        self.config = config or ModelConfig()
        self.image_gen_model = ImageGenerationModel(self.config)
        self.vision_model = VisionModel(self.config)
        logger.info("Model manager initialized")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current model configuration"""
        return {
            "image_generation_model": self.config.image_generation_model,
            "vision_model": self.config.vision_model,
            "image_size": self.config.image_size,
        }
    
    def set_image_generation_model(self, model_name: str, api_key: Optional[str] = None):
        """Change image generation model"""
        if api_key:
            self.config.image_generation_api_key = api_key
        self.image_gen_model.set_model(model_name)
    
    def set_vision_model(self, model_name: str, model_path: Optional[str] = None):
        """Change vision model"""
        self.vision_model.set_model(model_name, model_path)
    
    def generate_image(self, prompt: str, seed: Optional[int] = None) -> Optional[bytes]:
        """Generate image with current model"""
        return self.image_gen_model.generate_image(prompt, seed)
    
    def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze image with current vision model"""
        return self.vision_model.analyze_image(image_data)


# Global model manager instance
_model_manager: Optional[ModelManager] = None


def get_model_manager(config: Optional[ModelConfig] = None) -> ModelManager:
    """Get or create global model manager"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager(config)
    return _model_manager


def reset_model_manager():
    """Reset global model manager"""
    global _model_manager
    _model_manager = None
