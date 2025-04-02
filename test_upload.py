import requests

# Create a test image file
with open("test_image.jpg", "wb") as f:
    f.write(b"test image data")

# Test the upload endpoint
with open("test_image.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/cards/upload",
        files={"file": ("test_image.jpg", f, "image/jpeg")}
    )

print(response.json()) 