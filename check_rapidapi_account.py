#!/usr/bin/env python3
"""
Check RapidAPI account status and subscriptions
"""
import requests
import json

API_KEY = "ehxh49j41fofyu6i6ixfcs7f9"

print("="*70)
print("RapidAPI Account & Subscription Check")
print("="*70)
print()

# Test 1: Check if API key is valid at all
print("Test 1: Checking if API key is valid...")
print("-"*70)

# Try a different endpoint to see if the key itself works
test_apis = [
    {
        "name": "Twitter241",
        "host": "twitter241.p.rapidapi.com",
        "url": "https://twitter241.p.rapidapi.com/user",
        "params": {"username": "twitter"}
    },
    {
        "name": "Test API (Generic)",
        "host": "weatherapi-com.p.rapidapi.com",
        "url": "https://weatherapi-com.p.rapidapi.com/current.json",
        "params": {"q": "London"}
    }
]

for api in test_apis:
    print(f"\nTesting: {api['name']}")
    headers = {
        'X-RapidAPI-Key': API_KEY,
        'X-RapidAPI-Host': api['host']
    }

    try:
        response = requests.get(api['url'], headers=headers, params=api['params'], timeout=10)
        print(f"  Status: {response.status_code}")

        if response.status_code == 403:
            try:
                error_data = response.json()
                print(f"  Message: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"  Message: {response.text}")
        elif response.status_code == 200:
            print(f"  ✅ API key works! You're subscribed to {api['name']}")
        else:
            print(f"  Response: {response.text[:200]}")

    except Exception as e:
        print(f"  Error: {e}")

print()
print("="*70)
print("RESULTS & NEXT STEPS:")
print("="*70)
print()
print("If ALL tests show '403' with 'not subscribed' message:")
print("  → Your API key is valid, but you need to subscribe to APIs")
print()
print("How to subscribe to Twitter241:")
print("  1. Go to: https://rapidapi.com/twitter241/api/twitter241")
print("  2. Make sure you're logged in with the account for this API key")
print("  3. Click 'Subscribe to Test' button")
print("  4. Select a pricing plan:")
print("     - BASIC (Free): Usually 100-500 requests/month")
print("     - PRO: More requests (paid)")
print("     - Check current pricing on the page")
print("  5. Confirm subscription")
print()
print("After subscribing:")
print("  - Run: python3 test_api.py")
print("  - Or test in your Railway app")
print()
print("="*70)
