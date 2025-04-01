import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration():
    print("\nTesting user registration...")
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        # Make registration request
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=test_user
        )
        
        # Print response
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json().get("access_token") if response.status_code == 200 else None
        
    except Exception as e:
        print(f"Error during registration: {str(e)}")
        return None

def test_login():
    print("\nTesting user login...")
    
    # Test data
    login_data = {
        "username": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        # Make login request
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data=login_data
        )
        
        # Print response
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json().get("access_token") if response.status_code == 200 else None
        
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return None

def test_invalid_login():
    print("\nTesting invalid login...")
    
    # Test data with wrong password
    login_data = {
        "username": "test@example.com",
        "password": "wrongpassword"
    }
    
    try:
        # Make login request
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data=login_data
        )
        
        # Print response
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
        
    except Exception as e:
        print(f"Error during invalid login test: {str(e)}")

def main():
    print("Starting authentication tests...")
    
    # Test registration
    token = test_registration()
    
    # Test login
    token = test_login()
    
    # Test invalid login
    test_invalid_login()
    
    print("\nAuthentication tests completed!")

if __name__ == "__main__":
    main() 