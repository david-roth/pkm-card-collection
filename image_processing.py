import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
import pytesseract
from dataclasses import dataclass
import os
from fastapi import UploadFile

@dataclass
class CardRegion:
    x: int
    y: int
    width: int
    height: int
    confidence: float

class CardDetector:
    def __init__(self):
        # Load the pre-trained cascade classifier for card detection
        # You'll need to train this or use a pre-trained model
        self.card_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess the image for better card detection."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        return blurred

    def detect_card_regions(self, image: np.ndarray) -> List[CardRegion]:
        """Detect card regions in the image."""
        # Preprocess the image
        processed = self.preprocess_image(image)
        
        # Detect cards
        cards = self.card_cascade.detectMultiScale(
            processed,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Convert to CardRegion objects
        regions = []
        for (x, y, w, h) in cards:
            regions.append(CardRegion(x, y, w, h, 1.0))
        
        return regions

    def extract_card_text(self, image: np.ndarray, region: CardRegion) -> str:
        """Extract text from a card region using OCR."""
        # Extract the card region
        card = image[region.y:region.y+region.height, region.x:region.x+region.width]
        
        # Convert to grayscale for better OCR
        gray = cv2.cvtColor(card, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Perform OCR
        text = pytesseract.image_to_string(binary)
        return text.strip()

    def process_video_frame(self, frame: np.ndarray) -> List[Tuple[CardRegion, str]]:
        """Process a single video frame to detect and extract card information."""
        # Detect card regions
        regions = self.detect_card_regions(frame)
        
        # Extract text from each region
        results = []
        for region in regions:
            text = self.extract_card_text(frame, region)
            if text:
                results.append((region, text))
        
        return results

    def save_card_image(self, image: np.ndarray, region: CardRegion, output_path: str) -> None:
        """Save a detected card region as an image."""
        card = image[region.y:region.y+region.height, region.x:region.x+region.width]
        cv2.imwrite(output_path, card)

class VideoProcessor:
    def __init__(self, detector: CardDetector):
        self.detector = detector

    def process_video(self, video_path: str, output_dir: str) -> List[Tuple[CardRegion, str, float]]:
        """Process a video file to detect and extract card information."""
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")

        results = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process every 30th frame
            if frame_count % 30 == 0:
                frame_results = self.detector.process_video_frame(frame)
                for region, text in frame_results:
                    results.append((region, text, frame_count / cap.get(cv2.CAP_PROP_FPS)))
            
            frame_count += 1
        
        cap.release()
        return results

async def process_card_image(file: UploadFile) -> Dict[str, Any]:
    """Process an uploaded card image and extract text."""
    try:
        # For now, just return a mock success response
        # This will be replaced with AI image analysis later
        return {
            "success": True,
            "text": "Charizard"  # Mock text for testing
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        } 