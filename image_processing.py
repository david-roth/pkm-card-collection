from typing import Dict, Any
from fastapi import UploadFile

async def process_card_image(file: UploadFile) -> Dict[str, Any]:
    """Process an uploaded card image and extract text."""
    try:
        # Mock response for testing
        return {
            "success": True,
            "text": "Charizard"  # Mock text for testing
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        } 