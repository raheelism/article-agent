"""
Test script to diagnose connection issues.
Run: python test_connection.py
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force SSL bypass
os.environ['DISABLE_SSL_VERIFY'] = 'true'

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("CONNECTION DIAGNOSTICS")
print("=" * 60)

# Test 1: Check environment
print("\n1. Environment Variables:")
print(f"   GROQ_API_KEY: {'Set (' + os.getenv('GROQ_API_KEY', '')[:10] + '...)' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")
print(f"   DISABLE_SSL_VERIFY: {os.getenv('DISABLE_SSL_VERIFY', 'not set')}")
print(f"   HTTPS_PROXY: {os.getenv('HTTPS_PROXY', 'not set')}")

# Test 2: Basic HTTPS connectivity
print("\n2. Testing basic HTTPS connectivity...")
try:
    import httpx
    client = httpx.Client(verify=False, timeout=10.0)
    response = client.get("https://api.groq.com")
    print(f"   ✓ api.groq.com reachable (status: {response.status_code})")
except Exception as e:
    print(f"   ✗ api.groq.com FAILED: {e}")
    print("\n   >>> Your office firewall may be blocking api.groq.com")
    print("   >>> Ask IT to whitelist: api.groq.com")

# Test 3: Groq API with custom client
print("\n3. Testing Groq API with SSL bypass...")
try:
    from langchain_groq import ChatGroq
    
    http_client = httpx.Client(verify=False, timeout=30.0)
    
    llm = ChatGroq(
        model="llama-3.1-8b-instant",  # Use a small/fast model for testing
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
        http_client=http_client,
        timeout=30,
        max_retries=1
    )
    
    result = llm.invoke("Say hello in exactly 3 words")
    print(f"   ✓ Groq API working! Response: {result.content}")
    
except Exception as e:
    print(f"   ✗ Groq API FAILED: {e}")
    print("\n   Possible causes:")
    print("   - Firewall blocking api.groq.com")
    print("   - Corporate proxy required (set HTTPS_PROXY in .env)")
    print("   - API key invalid")

# Test 4: DuckDuckGo
print("\n4. Testing DuckDuckGo search...")
try:
    from ddgs import DDGS
    with DDGS(verify=False) as ddgs:
        results = list(ddgs.text("test", max_results=1))
        if results:
            print(f"   ✓ DuckDuckGo working! Found: {results[0].get('title', 'result')[:50]}")
        else:
            print("   ✓ DuckDuckGo reachable but no results")
except Exception as e:
    print(f"   ✗ DuckDuckGo FAILED: {e}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
