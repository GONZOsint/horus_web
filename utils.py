import os
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app
import base64
from io import BytesIO
import time

def save_base64_photo(base64_data: str, case_id: int) -> str:
    """
    Save a base64 encoded photo to a file.
    
    Args:
        base64_data (str): Base64 encoded image data
        case_id (int): ID of the case for creating a unique filename
    
    Returns:
        str: Relative path of the saved image
    """
    if not base64_data:
        return None
        
    try:
        # Create directory if it doesn't exist
        upload_dir = os.path.join(current_app.static_folder, 'case_photos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create unique filename
        new_filename = f"case_{case_id}.jpg"
        file_path = os.path.join(upload_dir, new_filename)
        
        # Decode base64 data
        image_data = base64.b64decode(base64_data)
        
        # Open and process image
        img = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large (max 800x800)
        max_size = (800, 800)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save optimized image
        img.save(file_path, 'JPEG', quality=85, optimize=True)
        
        # Return relative path for database storage
        return f"case_photos/{new_filename}"
    except Exception as e:
        current_app.logger.error(f"Error saving base64 photo: {str(e)}")
        return None

def save_case_photo(photo_data, case_id):
    """Save a case photo to the filesystem.
    
    Args:
        photo_data: Either a FileStorage object or a base64 string
        case_id: The ID of the case
        
    Returns:
        str: The relative path to the saved photo, or None if saving failed
    """
    try:
        if not photo_data:
            current_app.logger.warning("No photo data provided")
            return None
            
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.static_folder, 'case_photos')
        os.makedirs(upload_dir, exist_ok=True)
        current_app.logger.info(f"Using upload directory: {upload_dir}")
        
        # Generate unique filename
        filename = secure_filename(f'case_{case_id}_{int(time.time())}.jpg')
        filepath = os.path.join(upload_dir, filename)
        current_app.logger.info(f"Will save to: {filepath}")
        
        # Handle base64 data
        if isinstance(photo_data, str):
            current_app.logger.info(f"Processing string photo data, length: {len(photo_data)}")
            if photo_data.startswith('data:image'):
                # Extract the base64 data
                try:
                    base64_data = photo_data.split(',')[1]
                    current_app.logger.info(f"Extracted base64 data, length: {len(base64_data)}")
                    image_data = base64.b64decode(base64_data)
                    img = Image.open(BytesIO(image_data))
                    current_app.logger.info(f"Successfully decoded base64 image, size: {img.size}")
                except Exception as e:
                    current_app.logger.error(f"Error decoding base64 data: {str(e)}")
                    return None
            else:
                current_app.logger.error("Invalid photo data format: string does not start with 'data:image'")
                return None
        else:
            # Handle file upload
            current_app.logger.info("Processing file upload")
            img = Image.open(photo_data)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        # Resize image if it's too large
        max_size = (800, 800)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save optimized image
        img.save(filepath, 'JPEG', quality=85, optimize=True)
        current_app.logger.info(f"Saved image to {filepath}")
        
        # Return relative path for database storage
        return f"case_photos/{filename}"
        
    except Exception as e:
        current_app.logger.error(f"Error saving case photo: {str(e)}")
        return None 