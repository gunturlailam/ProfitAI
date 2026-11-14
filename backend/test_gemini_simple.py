"""
Simple Test untuk Gemini Integration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=" * 70)
print("GEMINI INTEGRATION - SIMPLE TEST")
print("=" * 70)

# Check API key
api_key = os.getenv("GEMINI_API_KEY", "").strip()
print(f"\n1. API Key Status:")
print(f"   Configured: {bool(api_key)}")
if api_key:
    print(f"   Key (first 20 chars): {api_key[:20]}...")
else:
    print("   ❌ API Key NOT found in .env")
    exit(1)

# Test import
print(f"\n2. Import Test:")
try:
    import google.generativeai as genai
    print("   ✓ google.generativeai imported")
    GENAI_AVAILABLE = True
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

# Configure Gemini
print(f"\n3. Gemini Configuration:")
try:
    genai.configure(api_key=api_key)
    print("   ✓ Gemini configured successfully")
except Exception as e:
    print(f"   ❌ Configuration failed: {e}")
    exit(1)

# Test simple generation
print(f"\n4. Test Generation:")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Jelaskan dalam 2 kalimat: Apa itu Current Ratio dalam analisis keuangan?
    """
    
    print("   Sending prompt to Gemini...")
    response = model.generate_content(prompt)
    
    if response and response.text:
        print("   ✓ Response received!")
        print(f"\n   Response:")
        print("   " + "-" * 66)
        for line in response.text.strip().split('\n'):
            print(f"   {line}")
        print("   " + "-" * 66)
    else:
        print("   ❌ Empty response")
        exit(1)
        
except Exception as e:
    print(f"   ❌ Generation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test JSON mode
print(f"\n5. Test JSON Output Mode:")
try:
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        generation_config={
            "temperature": 0.7,
            "response_mime_type": "application/json",
        }
    )
    
    prompt = """
    Berikan analisis dalam format JSON:
    {
        "explanation": "Penjelasan Current Ratio",
        "action": "Rekomendasi untuk pemilik UMKM"
    }
    """
    
    print("   Sending JSON prompt...")
    response = model.generate_content(prompt)
    
    if response and response.text:
        print("   ✓ JSON Response received!")
        print(f"\n   JSON Response:")
        print("   " + "-" * 66)
        
        import json
        try:
            parsed = json.loads(response.text)
            print(f"   {json.dumps(parsed, indent=2, ensure_ascii=False)}")
            print("   ✓ Valid JSON!")
        except json.JSONDecodeError as e:
            print(f"   ❌ Invalid JSON: {e}")
            print(f"   Raw: {response.text}")
        
        print("   " + "-" * 66)
    else:
        print("   ❌ Empty response")
        exit(1)
        
except Exception as e:
    print(f"   ❌ JSON generation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 70)
print("🎉 ALL TESTS PASSED - GEMINI INTEGRATION WORKING!")
print("=" * 70)
print("\nNext steps:")
print("1. Restart backend: uvicorn app.main:app --reload")
print("2. Test explain endpoint via API")
print()
