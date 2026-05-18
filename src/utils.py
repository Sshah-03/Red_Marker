"""
Utility functions for image processing and file handling
"""

import os
import io
from PIL import Image, ImageDraw, ImageFont
from src.config import (
    ALLOWED_EXTENSIONS, TEMP_DIR, MARKER_RADIUS, 
    MARKER_COLOR, MARKER_WIDTH
)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(content: bytes) -> tuple[int, int]:
    """
    Validate image content and return dimensions.
    
    Args:
        content: Image file content as bytes
        
    Returns:
        Tuple of (width, height)
        
    Raises:
        ValueError: If image is invalid
    """
    try:
        img = Image.open(io.BytesIO(content))
        return img.size
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")


def draw_markers_on_image(image_path: str, markers: list) -> bytes:
    """
    Draw markers on image and return as PNG bytes.
    
    Args:
        image_path: Path to the original image file
        markers: List of (x, y) tuples
        
    Returns:
        PNG image as bytes
    """
    try:
        # Open the original image
        img = Image.open(image_path).convert('RGB')
        
        # Draw markers if any exist
        if markers:
            draw = ImageDraw.Draw(img)
            for x, y in markers:
                # Draw hollow circle (ring)
                left = x - MARKER_RADIUS
                top = y - MARKER_RADIUS
                right = x + MARKER_RADIUS
                bottom = y + MARKER_RADIUS
                draw.ellipse(
                    [left, top, right, bottom],
                    outline=MARKER_COLOR,
                    width=MARKER_WIDTH
                )
        
        # Convert to bytes
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        return img_io.getvalue()
    except Exception as e:
        raise RuntimeError(f"Error processing image: {str(e)}")


def create_marker_detail_image(
    image_path: str,
    marker: tuple[int, int],
    explanation: str,
    crop_radius: int = 160,
    output_size: tuple[int, int] = (900, 700),
) -> bytes:
    """
    Create a precise marker-focused detail image from the original image.

    The output enlarges the region around the exact marker coordinate and adds a
    crosshair plus the user's explanation for review or export.
    """
    try:
        img = Image.open(image_path).convert('RGB')
        x, y = marker

        left = max(0, x - crop_radius)
        top = max(0, y - crop_radius)
        right = min(img.width, x + crop_radius)
        bottom = min(img.height, y + crop_radius)

        crop = img.crop((left, top, right, bottom))
        detail_w, detail_h = output_size
        caption_h = 170
        zoom_h = detail_h - caption_h
        crop.thumbnail((detail_w, zoom_h), Image.Resampling.LANCZOS)

        canvas = Image.new('RGB', output_size, (248, 248, 248))
        draw = ImageDraw.Draw(canvas)

        crop_x = (detail_w - crop.width) // 2
        crop_y = (zoom_h - crop.height) // 2
        canvas.paste(crop, (crop_x, crop_y))

        scale_x = crop.width / max(1, right - left)
        scale_y = crop.height / max(1, bottom - top)
        marker_x = crop_x + ((x - left) * scale_x)
        marker_y = crop_y + ((y - top) * scale_y)

        draw.line((marker_x - 28, marker_y, marker_x + 28, marker_y), fill='red', width=4)
        draw.line((marker_x, marker_y - 28, marker_x, marker_y + 28), fill='red', width=4)
        draw.ellipse((marker_x - 18, marker_y - 18, marker_x + 18, marker_y + 18), outline='red', width=4)
        draw.ellipse((marker_x - 4, marker_y - 4, marker_x + 4, marker_y + 4), fill='red')

        caption_top = zoom_h
        draw.rectangle((0, caption_top, detail_w, detail_h), fill=(18, 18, 18))

        try:
            title_font = ImageFont.truetype("Arial.ttf", 22)
            body_font = ImageFont.truetype("Arial.ttf", 18)
        except Exception:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()

        draw.text((24, caption_top + 18), f"Marker coordinate: ({x}, {y})", fill=(255, 255, 255), font=title_font)
        y_text = caption_top + 52
        for line in wrap_text(explanation.strip() or "No explanation provided.", 92)[:5]:
            draw.text((24, y_text), line, fill=(235, 235, 235), font=body_font)
            y_text += 24

        output = io.BytesIO()
        canvas.save(output, format='PNG')
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        raise RuntimeError(f"Error creating marker detail image: {str(e)}")


def crop_marker_region_image(
    image_path: str,
    marker: tuple[int, int],
    crop_radius: int = 160,
) -> bytes:
    """Return PNG bytes for the region around a marker."""
    try:
        img = Image.open(image_path).convert('RGB')
        x, y = marker
        left = max(0, x - crop_radius)
        top = max(0, y - crop_radius)
        right = min(img.width, x + crop_radius)
        bottom = min(img.height, y + crop_radius)

        crop = img.crop((left, top, right, bottom))
        output = io.BytesIO()
        crop.save(output, format='PNG')
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        raise RuntimeError(f"Error cropping marker region: {str(e)}")


def wrap_text(text: str, width: int) -> list[str]:
    """Wrap text by word count for PIL drawing."""
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
    return lines or [""]


def cleanup_session_files(image_path: str) -> None:
    """
    Remove temporary image file.
    
    Args:
        image_path: Path to the file to remove
    """
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception as e:
        print(f"Warning: Could not remove file {image_path}: {str(e)}")
