from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
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

from database import get_db, engine
import models
from models import User, Card

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Load environment variables
load_dotenv()

app = FastAPI(title="Pokemon Card Tracker API")

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
    email: str | None = None

class UserCreate(BaseModel):
    email: str
    password: str

class CardCreate(BaseModel):
    name: str
    collection: str
    market_price: float
    rarity: str
    image_url: str
    video_timestamp: str | None = None
    video_id: str | None = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
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
    # Save video temporarily
    video_path = f"temp_{file.filename}"
    with open(video_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Process video frames
    cap = cv2.VideoCapture(video_path)
    cards = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Extract text from frame
        text = pytesseract.image_to_string(frame)
        # Process text to identify cards
        # This is a simplified version - you'll need to implement proper card detection
        if "Pokemon" in text:
            # Create card entry
            card = Card(
                name="Detected Card",  # Implement proper card name detection
                collection="Detected Collection",  # Implement proper collection detection
                market_price=0.0,  # Implement price lookup
                rarity="Unknown",  # Implement rarity detection
                image_url="",  # Save frame as image
                video_timestamp=str(cap.get(cv2.CAP_PROP_POS_MSEC)),
                video_id=file.filename,
                owner_id=current_user.id
            )
            db.add(card)
            cards.append(card)
    
    cap.release()
    os.remove(video_path)
    db.commit()
    
    return {"message": f"Processed {len(cards)} cards"}

@app.post("/api/cards/upload")
async def upload_card(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Save image temporarily
    image_path = f"temp_{file.filename}"
    with open(image_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Process image
    image = cv2.imread(image_path)
    text = pytesseract.image_to_string(image)
    
    # Create card entry
    card = Card(
        name="Detected Card",  # Implement proper card name detection
        collection="Detected Collection",  # Implement proper collection detection
        market_price=0.0,  # Implement price lookup
        rarity="Unknown",  # Implement rarity detection
        image_url=file.filename,
        owner_id=current_user.id
    )
    
    db.add(card)
    db.commit()
    os.remove(image_path)
    
    return {"message": "Card processed successfully"}

@app.post("/api/cards/prompt")
async def process_card_prompt(
    card_data: CardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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