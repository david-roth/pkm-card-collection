import cv2
import numpy as np
from typing import Tuple, Optional, List
import pytesseract
from dataclasses import dataclass
import os

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
        """Preprocess image for better card detection."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply morphological operations
        kernel = np.ones((3,3), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return morph

    def detect_card_regions(self, image: np.ndarray) -> List[CardRegion]:
        """Detect potential card regions in the image."""
        processed = self.preprocess_image(image)
        
        # Detect edges
        edges = cv2.Canny(processed, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        card_regions = []
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio (Pokemon cards are typically 2.5" x 3.5")
            aspect_ratio = w / h
            if 0.6 <= aspect_ratio <= 0.8:  # Allow some flexibility
                # Calculate contour area
                area = cv2.contourArea(contour)
                # Filter by size
                if area > 1000:  # Minimum area threshold
                    card_regions.append(CardRegion(x, y, w, h, area / (image.shape[0] * image.shape[1])))
        
        return card_regions

    def extract_card_text(self, image: np.ndarray, region: CardRegion) -> str:
        """Extract text from a card region."""
        # Extract the card region
        card_img = image[region.y:region.y+region.height, region.x:region.x+region.width]
        
        # Preprocess for OCR
        gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Extract text
        text = pytesseract.image_to_string(thresh)
        return text.strip()

    def process_video_frame(self, frame: np.ndarray) -> List[Tuple[CardRegion, str]]:
        """Process a single video frame to detect and extract card information."""
        card_regions = self.detect_card_regions(frame)
        results = []
        
        for region in card_regions:
            text = self.extract_card_text(frame, region)
            if text:  # Only add if text was extracted
                results.append((region, text))
        
        return results

    def save_card_image(self, image: np.ndarray, region: CardRegion, output_path: str) -> None:
        """Save a detected card region as an image."""
        card_img = image[region.y:region.y+region.height, region.x:region.x+region.width]
        cv2.imwrite(output_path, card_img)

class VideoProcessor:
    def __init__(self, detector: CardDetector):
        self.detector = detector
        self.processed_frames = set()  # Track processed frames to avoid duplicates

    def process_video(self, video_path: str, output_dir: str) -> List[Tuple[CardRegion, str, float]]:
        """Process a video file and extract card information."""
        cap = cv2.VideoCapture(video_path)
        results = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Get current timestamp
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
            
            # Process frame
            frame_results = self.detector.process_video_frame(frame)
            
            # Save card images and add results
            for region, text in frame_results:
                # Generate unique filename
                filename = f"card_{len(results)}_{timestamp}.jpg"
                output_path = os.path.join(output_dir, filename)
                
                # Save card image
                self.detector.save_card_image(frame, region, output_path)
                
                results.append((region, text, timestamp))
        
        cap.release()
        return results 