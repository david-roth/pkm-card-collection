import requests
import json
import os
from datetime import datetime
import time

# Production URL - replace with your actual Render.com URL
BASE_URL = "https://pokemon-card-tracker.onrender.com"

def print_section(title):
    print("\n" + "="*50)
    print(f"Testing: {title}")
    print("="*50)

def test_health():
    print_section("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"Status Code: {response.status_code}")
        print("API Documentation is accessible")
        return response.status_code == 200
    except Exception as e:
        print(f"Error checking health: {str(e)}")
        return False

def test_registration():
    print_section("User Registration")
    
    # Generate unique email using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_user = {
        "email": f"test{timestamp}@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=test_user
        )
        
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print(f"Successfully registered user: {test_user['email']}")
            return response.json().get("access_token")
        else:
            print("Registration failed")
            return None
            
    except Exception as e:
        print(f"Error during registration: {str(e)}")
        return None

def test_login(email, password):
    print_section("User Login")
    
    login_data = {
        "username": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data=login_data
        )
        
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("Login successful")
            return response.json().get("access_token")
        else:
            print("Login failed")
            return None
            
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return None

def test_card_upload(token):
    print_section("Card Upload")
    
    # Create a test image file
    test_image_path = "test_card.jpg"
    try:
        with open(test_image_path, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(
                f"{BASE_URL}/api/cards/upload",
                headers=headers,
                files=files
            )
            
            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            
            return response.status_code == 200
            
    except Exception as e:
        print(f"Error during card upload: {str(e)}")
        return False

def test_collection(token):
    print_section("Collection Retrieval")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/collection",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error retrieving collection: {str(e)}")
        return False

def test_manual_card_add(token):
    print_section("Manual Card Addition")
    
    card_data = {
        "name": "Charizard",
        "collection": "Base Set",
        "market_price": 100.0,
        "rarity": "Rare Holo",
        "image_url": "https://example.com/card.jpg"
    }
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{BASE_URL}/api/cards/prompt",
            headers=headers,
            json=card_data
        )
        
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error adding card manually: {str(e)}")
        return False

def main():
    print("Starting Production API Tests")
    print(f"Testing against: {BASE_URL}")
    
    # Test health check
    if not test_health():
        print("Health check failed. Stopping tests.")
        return
    
    # Test registration and login
    token = test_registration()
    if not token:
        print("Registration failed. Stopping tests.")
        return
    
    # Wait a moment before login
    time.sleep(1)
    
    # Test login with the registered user
    login_token = test_login(f"test{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com", "testpassword123")
    if not login_token:
        print("Login failed. Stopping tests.")
        return
    
    # Test protected endpoints
    test_card_upload(login_token)
    test_collection(login_token)
    test_manual_card_add(login_token)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 