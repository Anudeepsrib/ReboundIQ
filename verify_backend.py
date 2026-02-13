import requests
import json
import time

API_URL = "http://localhost:8000/api/v1/assistant/analyze_message"
API_KEY = "dev_test_key_12345"

payload = {
    "message_text": "Hey, I saw your profile and thought you'd be a great fit for our Sr. Python Developer role at TechCorp. We are looking for someone with FastAPI experience.",
    "sender_name": "John Doe",
    "company_name": "TechCorp",
    "user_resume_context": "I am a Senior Backend Engineer with 5 years experience in Python, FastAPI, and AWS. I built a RAG system recently.",
    "desired_tone": "professional"
}

headers = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY
}

def verify():
    print(f"Sending request to {API_URL}...")
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            print("SUCCESS! Backend responded:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"FAILURE! Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Wait a bit for server to start if run immediately after
    time.sleep(2)
    verify()
