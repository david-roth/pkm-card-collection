# Pokemon Card Tracker API

An API for processing Pokemon card booster opening videos and managing card collections. The API processes videos to extract card information and creates reports in Notion.

## Features

- Video processing for card recognition
- Manual card upload and processing
- Card collection management
- Market price lookup
- Notion integration for report generation
- Authentication system

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file with:
```
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_database_id
SECRET_KEY=your_secret_key
```

3. Install Tesseract OCR:
- Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`

4. Run the API:
```bash
uvicorn main:app --reload
```

## API Endpoints

- POST `/api/videos/process`: Process a video file
- POST `/api/cards/upload`: Manually upload a card image
- POST `/api/cards/prompt`: Process card information from a prompt
- GET `/api/collection`: Get user's card collection
- POST `/api/auth/register`: Register a new user
- POST `/api/auth/login`: Login user

## Deployment

The API is configured for deployment on Render.com. Follow these steps:

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables in Render dashboard
4. Deploy!

## License

MIT 