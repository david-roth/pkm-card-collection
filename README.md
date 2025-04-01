# Pokemon Card Tracker API

A FastAPI-based application for tracking Pokemon card collections, processing card images and videos, and integrating with Notion for collection management.

## Features

- 🔐 User authentication with JWT tokens
- 📸 Card detection from images and videos
- 💰 Automatic market price lookup
- 📊 Collection management
- 🔄 Notion integration for collection tracking
- 🎥 Video processing for booster pack openings

## Prerequisites

- Python 3.9+
- Tesseract OCR installed on your system
- Pokemon TCG API key
- Notion API token and database ID

### Installing Tesseract OCR

#### Windows
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. Add Tesseract to your system PATH

#### Linux
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### macOS
```bash
brew install tesseract
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/david-roth/pkm-card-collection.git
cd pkm-card-collection
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
POKEMON_TCG_API_KEY=your-pokemon-tcg-api-key
NOTION_TOKEN=your-notion-token
NOTION_DATABASE_ID=your-notion-database-id
```

5. Run the application:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

### Authentication

#### Register a new user
```http
POST /api/auth/register
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "your-password"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=your-password
```

Both endpoints return a JWT token that should be included in subsequent requests:
```http
Authorization: Bearer your-jwt-token
```

### Card Processing

#### Upload a single card image
```http
POST /api/cards/upload
Authorization: Bearer your-jwt-token
Content-Type: multipart/form-data

file: [image_file]
```

#### Process a video of card openings
```http
POST /api/videos/process
Authorization: Bearer your-jwt-token
Content-Type: multipart/form-data

file: [video_file]
```

#### Add a card manually
```http
POST /api/cards/prompt
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
    "name": "Charizard",
    "collection": "Base Set",
    "market_price": 100.0,
    "rarity": "Rare Holo",
    "image_url": "https://example.com/card.jpg"
}
```

#### Get your collection
```http
GET /api/collection
Authorization: Bearer your-jwt-token
```

## Example Usage

### Using cURL

1. Register a new user:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your-password"}'
```

2. Login:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=your-password"
```

3. Upload a card image:
```bash
curl -X POST http://localhost:8000/api/cards/upload \
  -H "Authorization: Bearer your-jwt-token" \
  -F "file=@path/to/card.jpg"
```

### Using Python requests

```python
import requests

# Register
response = requests.post(
    "http://localhost:8000/api/auth/register",
    json={"email": "user@example.com", "password": "your-password"}
)

# Login
response = requests.post(
    "http://localhost:8000/api/auth/login",
    data={"username": "user@example.com", "password": "your-password"}
)
token = response.json()["access_token"]

# Upload a card
with open("card.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/cards/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": f}
    )
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- 400: Bad Request (invalid input)
- 401: Unauthorized (invalid credentials)
- 404: Not Found (resource not found)
- 422: Validation Error (invalid data format)

## Development

### Running Tests
```bash
pytest
```

### Code Style
```bash
black .
flake8
```

## Deployment

The application is configured for deployment on Render.com. See `render.yaml` for deployment configuration.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details 