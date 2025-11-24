#!/usr/bin/env python3
"""
Test script to verify Twitter241 API connection
"""
import requests
import json

# Your API key (change this if needed)
API_KEY = "ehxh49j41fofyu6i6ixfcs7f9"
API_HOST = "twitter241.p.rapidapi.com"
BASE_URL = "https://twitter241.p.rapidapi.com"

headers = {
    'X-RapidAPI-Key': API_KEY,
    'X-RapidAPI-Host': API_HOST
}

print("="*60)
print("Twitter241 API Connection Test")
print("="*60)
print(f"\nAPI Host: {API_HOST}")
print(f"API Key: {API_KEY[:10]}...{API_KEY[-5:]}")
print()

# Test 1: Simple user lookup
test_username = "nyxcipher"
print(f"Testing username: {test_username}")
print("-"*60)

try:
    url = f"{BASE_URL}/user"
    params = {'username': test_username}

    print(f"Request URL: {url}")
    print(f"Parameters: {params}")
    print(f"Headers: X-RapidAPI-Key: {API_KEY[:10]}...")
    print()

    response = requests.get(url, headers=headers, params=params, timeout=30)

    print(f"Response Status Code: {response.status_code}")
    print(f"Response Headers:")
    for key, value in response.headers.items():
        if 'ratelimit' in key.lower() or 'quota' in key.lower():
            print(f"  {key}: {value}")
    print()

    if response.status_code == 200:
        print("✅ SUCCESS! API is working correctly.")
        data = response.json()
        print(f"\nResponse preview:")
        print(json.dumps(data, indent=2)[:500])

    elif response.status_code == 403:
        print("❌ ERROR: 403 Forbidden")
        print("\nPossible causes:")
        print("  1. API key is invalid or expired")
        print("  2. Not subscribed to Twitter241 API on RapidAPI")
        print("  3. Subscription plan doesn't include this endpoint")
        print("  4. Rate limit exceeded")
        print()
        print("Response body:")
        print(response.text)

    elif response.status_code == 429:
        print("❌ ERROR: 429 Too Many Requests")
        print("You've exceeded your rate limit. Wait and try again.")

    else:
        print(f"❌ ERROR: Unexpected status code {response.status_code}")
        print("Response body:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"❌ Network Error: {e}")

print()
print("="*60)
print("Next Steps:")
print("="*60)
print("1. Visit https://rapidapi.com/twitter241/api/twitter241")
print("2. Check your subscription status and quota")
print("3. Test the endpoint directly in RapidAPI console")
print("4. Verify your API key is correct")
print("="*60)
