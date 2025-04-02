from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from card_processing import router as card_router
from config import get_settings
from notion_integration import verify_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        database_id = os.getenv("NOTION_DATABASE_ID")
        if not database_id:
            logger.error("NOTION_DATABASE_ID environment variable is not set")
            yield
            return
            
        logger.info(f"Verifying Notion database connection... Database ID: {database_id}")
        verify_database(database_id)
        logger.info("Notion database connection verified successfully")
    except Exception as e:
        logger.error(f"Error verifying database: {str(e)}")
        logger.error(f"Database ID: {database_id}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(traceback.format_exc())
    yield
    # Shutdown
    logger.info("Shutting down application...")

# Initialize FastAPI app with lifespan
app = FastAPI(title="Pokemon Card Tracker", lifespan=lifespan)

# Load settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(card_router, prefix="/api/cards", tags=["cards"])

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": str(request.base_url)
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.middleware("http")
async def log_requests(request, call_next):
    """Log all requests."""
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response 