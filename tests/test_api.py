import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_search_endpoint():
    response = client.get("/api/cards/search", params={"query": "Pikachu"})
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data
    assert "cards" in data

def test_upload_endpoint():
    # Create a dummy file for testing
    files = {"file": ("test.jpg", b"dummy image data", "image/jpeg")}
    response = client.post("/api/cards/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data
    assert "cards" in data

def test_report_endpoint():
    response = client.post(
        "/api/cards/report",
        params={
            "query": "Pikachu",
            "set_id": "sv3",
            "group_id": "test_group"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data
    assert "cards" in data 