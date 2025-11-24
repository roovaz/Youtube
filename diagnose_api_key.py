#!/usr/bin/env python3
"""
Comprehensive API key diagnostic tool
"""
import os
import requests
import sys

print("="*70)
print("Twitter241 API Key Diagnostic")
print("="*70)
print()

# Check environment variables
print("Step 1: Checking Environment Variables")
print("-"*70)

rapidapi_key = os.environ.get('RAPIDAPI_KEY')
twitter_api_key = os.environ.get('TWITTER_API_KEY')

print(f"RAPIDAPI_KEY exists: {rapidapi_key is not None}")
if rapidapi_key:
    print(f"RAPIDAPI_KEY value: {rapidapi_key}")
    print(f"RAPIDAPI_KEY length: {len(rapidapi_key)}")
    print(f"RAPIDAPI_KEY repr: {repr(rapidapi_key)}")

print()
print(f"TWITTER_API_KEY exists: {twitter_api_key is not None}")
if twitter_api_key:
    print(f"TWITTER_API_KEY value: {twitter_api_key}")
    print(f"TWITTER_API_KEY length: {len(twitter_api_key)}")
    print(f"TWITTER_API_KEY repr: {repr(twitter_api_key)}")

print()

# Determine which key to use (same logic as config.py)
api_key = os.environ.get('RAPIDAPI_KEY') or os.environ.get('TWITTER_API_KEY', '')

print(f"Final API key being used: {api_key}")
print(f"Final API key length: {len(api_key)}")
print(f"Final API key repr: {repr(api_key)}")

if not api_key:
    print("\n❌ ERROR: No API key found!")
    print("Make sure TWITTER_API_KEY or RAPIDAPI_KEY is set")
    sys.exit(1)

print()
print("Step 2: Testing API Call")
print("-"*70)

# Test the API call
url = "https://twitter241.p.rapidapi.com/user"
headers = {
    'X-RapidAPI-Key': api_key,
    'X-RapidAPI-Host': 'twitter241.p.rapidapi.com'
}
params = {'username': 'twitter'}

print(f"URL: {url}")
print(f"Headers:")
print(f"  X-RapidAPI-Key: {api_key}")
print(f"  X-RapidAPI-Host: twitter241.p.rapidapi.com")
print(f"Params: {params}")
print()

try:
    response = requests.get(url, headers=headers, params=params, timeout=30)

    print(f"Status Code: {response.status_code}")
    print(f"Response Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    print()

    if response.status_code == 200:
        print("✅ SUCCESS! API key is working correctly!")
    elif response.status_code == 401:
        print("❌ ERROR 401: Unauthorized")
        print("\nThis means the API key is being rejected.")
        print("\nPossible causes:")
        print("  1. The API key is incorrect")
        print("  2. The API key has extra spaces/characters")
        print("  3. The API key has been revoked/expired")
        print("\nResponse body:")
        print(response.text)
    elif response.status_code == 403:
        print("❌ ERROR 403: Forbidden")
        print("This means you need to subscribe to the API")
        print("\nResponse body:")
        print(response.text)
    else:
        print(f"❌ ERROR {response.status_code}")
        print("\nResponse body:")
        print(response.text)

except Exception as e:
    print(f"❌ Network Error: {e}")

print()
print("="*70)
print("RECOMMENDATIONS:")
print("="*70)
print()
print("1. Double-check your API key at:")
print("   https://rapidapi.com/developer/apps")
print()
print("2. Make sure you're using the correct key from the Twitter241 API")
print()
print("3. Verify the key doesn't have extra spaces or line breaks")
print()
print("4. Check if the key is from the correct RapidAPI account")
print()
print("="*70)
