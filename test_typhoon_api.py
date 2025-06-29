#!/usr/bin/env python3
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_typhoon_api():
    """Test Typhoon API connectivity"""
    api_key = os.getenv('TYPHOON_API_KEY')
    if not api_key:
        print("❌ TYPHOON_API_KEY not found in .env file")
        return False
    
    print(f"✅ Found API key: {api_key[:10]}...")
    
    url = "https://api.opentyphoon.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "typhoon-v2.1-12b-instruct",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. You must answer only in Thai."
            },
            {
                "role": "user",
                "content": "Translate this to Thai: Hello world"
            }
        ],
        "max_tokens": 512,
        "temperature": 0.6,
        "top_p": 0.95,
        "repetition_penalty": 1.05,
        "stream": False
    }
    
    print("🔍 Testing Typhoon API connection...")
    
    try:
        # Test with different timeout and SSL settings
        print("Attempt 1: Standard request...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Error: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    
    # Try alternative approaches
    print("\n🔧 Trying alternative approaches...")
    
    try:
        print("Attempt 2: With SSL verification disabled...")
        response = requests.post(url, headers=headers, json=data, timeout=30, verify=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response: {result['choices'][0]['message']['content']}")
            return True
    except Exception as e:
        print(f"❌ Still failed: {e}")
    
    print("\n💡 Troubleshooting suggestions:")
    print("1. Check your internet connection")
    print("2. Verify the API key is correct")
    print("3. Check if Typhoon API is accessible from your network")
    print("4. Try using a VPN if you're behind a firewall")
    print("5. Contact Typhoon support if the issue persists")
    
    return False

if __name__ == "__main__":
    test_typhoon_api() 