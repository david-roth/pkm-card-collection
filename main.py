from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Union, Optional
import cv2
import pytesseract
import os
from dotenv import load_dotenv
from notion_client import Client
import requests
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import json
import tempfile
from pokemon_tcg import PokemonTCGAPI
from image_processing import CardDetector, VideoProcessor
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database import get_db, engine
import models
from models import User, Card

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Pokemon Card Tracker API",
    description="API for managing Pokemon card collections with OCR capabilities",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize APIs and processors
pokemon_tcg = PokemonTCGAPI()
card_detector = CardDetector()
video_processor = VideoProcessor(card_detector)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Notion client
notion = Client(auth=os.getenv("NOTION_TOKEN"))

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str

class CardCreate(BaseModel):
    name: str
    collection: str
    market_price: float
    rarity: str
    image_url: str
    video_timestamp: Optional[str] = None
    video_id: Optional[str] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

# Authentication endpoints
@app.post("/api/auth/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Card processing endpoints
@app.post("/api/videos/process")
async def process_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cards = []
    
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save video temporarily
        video_path = os.path.join(temp_dir, file.filename)
        with open(video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process video
        results = video_processor.process_video(video_path, temp_dir)
        
        for region, text, timestamp in results:
            # Extract card information from OCR text
            card_info = pokemon_tcg.extract_card_info(text)
            if card_info and card_info["name"]:
                # Search for card in Pokemon TCG API
                card_data = pokemon_tcg.search_card(card_info["name"], card_info["set"])
                if card_data:
                    # Get market price
                    market_price = pokemon_tcg.get_card_market_price(card_data["id"])
                    
                    # Create card entry
                    card = Card(
                        name=card_data["name"],
                        collection=card_data["set"]["name"],
                        market_price=market_price or 0.0,
                        rarity=card_data["rarity"],
                        image_url=os.path.join(temp_dir, f"card_{len(cards)}_{timestamp}.jpg"),
                        video_timestamp=str(timestamp),
                        video_id=file.filename,
                        owner_id=current_user.id
                    )
                    db.add(card)
                    cards.append(card)
        
        db.commit()
    
    return {"message": f"Processed {len(cards)} cards"}

@app.post("/api/cards/upload")
async def upload_card(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save image temporarily
        image_path = os.path.join(temp_dir, file.filename)
        with open(image_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process image
        image = cv2.imread(image_path)
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )
        
        # Detect card regions
        card_regions = card_detector.detect_card_regions(image)
        if not card_regions:
            raise HTTPException(
                status_code=400,
                detail="No card detected in image"
            )
        
        # Extract text from the first detected card
        text = card_detector.extract_card_text(image, card_regions[0])
        if not text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from card"
            )
        
        # Extract card information from OCR text
        card_info = pokemon_tcg.extract_card_info(text)
        if not card_info or not card_info["name"]:
            raise HTTPException(
                status_code=400,
                detail="Could not extract card information from text"
            )
        
        # Search for card in Pokemon TCG API
        card_data = pokemon_tcg.search_card(card_info["name"], card_info["set"])
        if not card_data:
            raise HTTPException(
                status_code=404,
                detail="Card not found in Pokemon TCG database"
            )
        
        # Get market price
        market_price = pokemon_tcg.get_card_market_price(card_data["id"])
        
        # Save card image
        output_path = os.path.join(temp_dir, "card.jpg")
        card_detector.save_card_image(image, card_regions[0], output_path)
        
        # Create card entry
        card = Card(
            name=card_data["name"],
            collection=card_data["set"]["name"],
            market_price=market_price or 0.0,
            rarity=card_data["rarity"],
            image_url=output_path,
            owner_id=current_user.id
        )
        
        db.add(card)
        db.commit()
        
        # Create Notion entry
        notion_page = notion.pages.create(
            parent={"database_id": os.getenv("NOTION_DATABASE_ID")},
            properties={
                "Name": {"title": [{"text": {"content": card.name}}]},
                "Collection": {"rich_text": [{"text": {"content": card.collection}}]},
                "Market Price": {"number": card.market_price},
                "Rarity": {"select": {"name": card.rarity}},
                "Owner": {"rich_text": [{"text": {"content": current_user.email}}]}
            }
        )
        
        card.notion_page_id = notion_page["id"]
        db.commit()
    
    return {"message": "Card processed successfully"}

@app.post("/api/cards/prompt")
async def process_card_prompt(
    card_data: CardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Search for card in Pokemon TCG API
    tcg_card = pokemon_tcg.search_card(card_data.name, card_data.collection)
    if tcg_card:
        # Update card data with TCG information
        card_data.collection = tcg_card["set"]["name"]
        card_data.rarity = tcg_card["rarity"]
        market_price = pokemon_tcg.get_card_market_price(tcg_card["id"])
        if market_price:
            card_data.market_price = market_price
    
    card = Card(**card_data.dict(), owner_id=current_user.id)
    db.add(card)
    db.commit()
    
    # Create Notion entry
    notion_page = notion.pages.create(
        parent={"database_id": os.getenv("NOTION_DATABASE_ID")},
        properties={
            "Name": {"title": [{"text": {"content": card.name}}]},
            "Collection": {"rich_text": [{"text": {"content": card.collection}}]},
            "Market Price": {"number": card.market_price},
            "Rarity": {"select": {"name": card.rarity}},
            "Owner": {"rich_text": [{"text": {"content": current_user.email}}]}
        }
    )
    
    card.notion_page_id = notion_page["id"]
    db.commit()
    
    return {"message": "Card processed successfully"}

@app.get("/api/collection")
async def get_collection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cards = db.query(Card).filter(Card.owner_id == current_user.id).all()
    return cards

@app.get("/")
async def root(request: Request):
    """Root endpoint that serves the landing page"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": request.base_url
        }
    ) 