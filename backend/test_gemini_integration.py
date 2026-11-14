"""
Test Script untuk Gemini Integration
=====================================

Script ini untuk test LLM adapter dan endpoint explain ratio.

Usage:
1. Pastikan backend running: uvicorn app.main:app --reload
2. Pastikan GEMINI_API_KEY sudah diset di .env
3. Run: python test_gemini_integration.py
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

def test_llm_adapter():
    """Test LLM adapter module directly."""
    print("=" * 70)
    print("TEST 1: LLM Adapter Module")
    print("=" * 70)
    
    from app.llm_adapter import get_llm_status, generate_ratio_explanation
    
    # Check status
    status = get_llm_status()
    print("\nLLM Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    if not status["llm_enabled"]:
        print("\n⚠️  LLM NOT ENABLED - Check GEMINI_API_KEY in .env")
        return False
    
    # Test explanation generation
    print("\n" + "-" * 70)
    print("Generating explanation for Current Ratio...")
    print("-" * 70)
    
    result = generate_ratio_explanation(
        ratio_code="CR",
        ratio_name="Current Ratio",
        category="liquidity",
        value="4.7032",
        band="above_target",
        direction="higher",
        data_quality="ok",
        target="1.5000",
        warning_threshold="1.2000",
        critical_threshold="1.0000",
        unit="x",
        period={"from": "2026-10-01", "to": "2026-10-31"}
    )
    
    print(f"\nSource: {result.get('source')}")
    print(f"LLM Available: {result.get('llm_available')}")
    print(f"Model: {result.get('model', 'N/A')}")
    
    if result.get('fallback_reason'):
        print(f"Fallback Reason: {result['fallback_reason']}")
    
    print("\nExplanation:")
    print("-" * 70)
    print(result.get('explanation', 'No explanation'))
    
    print("\nAction:")
    print("-" * 70)
    print(result.get('action', 'No action'))
    
    if result.get('warning'):
        print("\nWarning:")
        print("-" * 70)
        print(result['warning'])
    
    return True


def test_api_endpoint():
    """Test API endpoint dengan requests."""
    print("\n" + "=" * 70)
    print("TEST 2: API Endpoint /api/v1/ratios/{code}/explain")
    print("=" * 70)
    
    try:
        import requests
    except ImportError:
        print("\n⚠️  requests not installed. Skip API test.")
        print("   Install: pip install requests")
        return False
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code != 200:
            print("\n⚠️  Backend not healthy")
            return False
    except requests.exceptions.ConnectionError:
        print("\n⚠️  Backend not running at http://localhost:8000")
        print("   Start backend: uvicorn app.main:app --reload")
        return False
    
    print("\n✓ Backend is running")
    
    # Login first
    print("\nAttempting login...")
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json={
            "email": "demo@profitai.id",
            "password": "demo123"
        }
    )
    
    if login_response.status_code != 200:
        print(f"\n⚠️  Login failed: {login_response.status_code}")
        print("   Response:", login_response.text)
        print("\n   Note: You might need to register first or use correct credentials")
        return False
    
    token = login_response.json().get("access_token")
    print("✓ Login successful")
    
    # Call explain endpoint
    print("\nCalling /api/v1/ratios/CR/explain...")
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "from": "2026-10-01",
        "to": "2026-10-31"
    }
    
    explain_response = requests.post(
        "http://localhost:8000/api/v1/ratios/CR/explain",
        headers=headers,
        params=params
    )
    
    if explain_response.status_code != 200:
        print(f"\n⚠️  Explain failed: {explain_response.status_code}")
        print("   Response:", explain_response.text)
        return False
    
    result = explain_response.json()
    
    print("\n" + "-" * 70)
    print(f"Ratio: {result.get('ratio_name')} ({result.get('ratio_code')})")
    print(f"Value: {result.get('display')}")
    print(f"Band: {result.get('band')}")
    print(f"Source: {result.get('source')}")
    print(f"LLM Available: {result.get('llm_available')}")
    
    print("\nExplanation:")
    print("-" * 70)
    print(result.get('explanation', 'No explanation'))
    
    print("\nAction:")
    print("-" * 70)
    print(result.get('action', 'No action'))
    
    print("\n✓ API test successful!")
    return True


def main():
    """Run all tests."""
    print("\n")
    print("🚀 " * 20)
    print("    PROFITAI - GEMINI INTEGRATION TEST")
    print("🚀 " * 20)
    
    # Test 1: LLM Adapter
    test1_ok = test_llm_adapter()
    
    # Test 2: API Endpoint
    test2_ok = test_api_endpoint()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Test 1 (LLM Adapter): {'✓ PASS' if test1_ok else '✗ FAIL'}")
    print(f"Test 2 (API Endpoint): {'✓ PASS' if test2_ok else '✗ FAIL'}")
    print("=" * 70)
    
    if test1_ok and test2_ok:
        print("\n🎉 ALL TESTS PASSED!")
    elif test1_ok:
        print("\n⚠️  LLM Adapter works, but API test failed (backend might not be running)")
    else:
        print("\n❌ TESTS FAILED - Check configuration")
    
    print("\n")


if __name__ == "__main__":
    main()
