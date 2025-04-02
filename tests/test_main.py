import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
from datetime import datetime

# Mock settings before importing main
mock_settings = MagicMock()
mock_settings.NOTION_TOKEN = "test_notion_token"
mock_settings.NOTION_DATABASE_ID = "test_database_id"
mock_settings.POKEMON_TCG_API_KEY = "test_api_key"
mock_settings.CORS_ORIGINS = ["*"]

with patch("config.get_settings", return_value=mock_settings):
    from main import app

client = TestClient(app)

def test_read_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to Pokemon Card Tracker" in response.text

@patch('pokemon_tcg_api.PokemonTCGAPI.search_card')
def test_search_card(mock_search_card):
    """Test card search functionality."""
    # Mock the Pokemon TCG API response
    mock_cards = [
        {
            "id": "test-id-1",
            "name": "Charizard",
            "set": {
                "name": "Base Set",
                "id": "base1"
            },
            "rarity": "Rare",
            "number": "4",
            "market_price": 100.0,
            "images": {
                "small": "https://example.com/charizard1.jpg",
                "large": "https://example.com/charizard1_large.jpg"
            }
        },
        {
            "id": "test-id-2",
            "name": "Charizard",
            "set": {
                "name": "Gym Challenge",
                "id": "gym2"
            },
            "rarity": "Rare Holo",
            "number": "2",
            "market_price": 200.0,
            "images": {
                "small": "https://example.com/charizard2.jpg",
                "large": "https://example.com/charizard2_large.jpg"
            }
        }
    ]
    mock_search_card.return_value = mock_cards

    response = client.get(
        "/api/cards/search",
        params={
            "query": "Charizard",
            "set_id": "base1"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["cards"]) == 2
    assert data["cards"][0]["name"] == "Charizard"
    assert data["cards"][1]["name"] == "Charizard"
    assert data["cards"][0]["collection"] == "Base Set"
    assert data["cards"][1]["collection"] == "Gym Challenge"

@patch('pokemon_tcg_api.PokemonTCGAPI.search_card')
def test_search_card_not_found(mock_search_card):
    """Test card search when no card is found."""
    mock_search_card.return_value = []

    response = client.get(
        "/api/cards/search",
        params={
            "query": "NonExistentCard",
            "set_id": "base1"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "No cards found" in data["message"]

@patch('image_processing.process_card_image')
@patch('pokemon_tcg_api.PokemonTCGAPI.search_card')
def test_upload_card(mock_search_card, mock_process_image):
    """Test card image upload endpoint."""
    # Mock image processing result
    mock_process_image.return_value = {
        "success": True,
        "text": "Charizard"
    }

    # Mock Pokemon TCG API response
    mock_search_card.return_value = [{
        "id": "test-id-1",
        "name": "Charizard",
        "set": {
            "name": "Base Set",
            "id": "base1"
        },
        "rarity": "Rare",
        "number": "4",
        "market_price": 100.0,
        "images": {
            "small": "https://example.com/charizard1.jpg",
            "large": "https://example.com/charizard1_large.jpg"
        }
    }]

    # Create a test image file
    test_image_path = "test_image.jpg"
    with open(test_image_path, "wb") as f:
        f.write(b"fake image data")

    try:
        with open(test_image_path, "rb") as f:
            response = client.post(
                "/api/cards/upload",
                files={"file": ("test_image.jpg", f, "image/jpeg")}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Cards processed successfully" in data["message"]
        assert "cards" in data
        assert len(data["cards"]) > 0
        assert data["cards"][0]["name"] == "Charizard"
    finally:
        # Clean up test file
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

def test_create_card_report():
    """Test the card report creation endpoint."""
    # Mock the create_card_report method
    with patch("notion_integration.NotionIntegration.create_card_report") as mock_create_report, \
         patch("notion_integration.NotionIntegration.check_existing_card") as mock_check_exists, \
         patch("pokemon_tcg_api.PokemonTCGAPI.search_card") as mock_search:
        
        # Set up mock data
        mock_card = {
            "id": "test-card-id",
            "name": "Test Card",
            "set": {"name": "Test Set"},
            "rarity": "Common",
            "number": "1",
            "market_price": 10.0,
            "images": {"large": "https://example.com/image.jpg"}
        }
        
        # Configure mocks
        mock_search.return_value = [mock_card]
        mock_check_exists.return_value = False
        mock_create_report.return_value = "test-page-id"
        
        # Make the request
        response = client.post("/api/cards/report?query=Test&set_id=test-set&group_id=TO-BE-CHECKED")
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully added 1 cards to Notion" in data["message"]
        assert len(data["cards"]) == 1
        assert data["cards"][0]["name"] == "Test Card"
        assert data["cards"][0]["group_id"] == "TO-BE-CHECKED"
        
        # Verify create_card_report was called with correct parameters
        mock_create_report.assert_called_once()
        call_args = mock_create_report.call_args[0]
        assert call_args[0]["name"] == "Test Card"
        assert call_args[0]["group_id"] == "TO-BE-CHECKED" 