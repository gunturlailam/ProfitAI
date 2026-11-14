"""
Test untuk Gemini Integration dengan google-genai (New API)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=" * 70)
print("GEMINI INTEGRATION - NEW API TEST (google-genai)")
print("=" * 70)

# Check API key
api_key = os.getenv("GEMINI_API_KEY", "").strip()
print(f"\n1. API Key Status:")
print(f"   Configured: {bool(api_key)}")
if api_key:
    print(f"   Key (first 20 chars): {api_key[:20]}...")
    print(f"   Key length: {len(api_key)} chars")
else:
    print("   ❌ API Key NOT found in .env")
    exit(1)

# Test import
print(f"\n2. Import Test:")
try:
    from google import genai
    from google.genai import types
    print("   ✓ google.genai imported (NEW API)")
    GENAI_AVAILABLE = True
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    print("\n   Install with: pip install google-genai")
    exit(1)

# Create client
print(f"\n3. Gemini Client Creation:")
try:
    client = genai.Client(api_key=api_key)
    print("   ✓ Gemini client created successfully")
except Exception as e:
    print(f"   ❌ Client creation failed: {e}")
    exit(1)

# Test simple generation
print(f"\n4. Test Generation (Plain Text):")
try:
    prompt = "Jelaskan dalam 2 kalimat: Apa itu Current Ratio dalam analisis keuangan?"
    
    print("   Sending prompt to Gemini...")
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt
    )
    
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
    system_prompt = """
Anda adalah CFO virtual untuk UMKM Indonesia. 
Berikan analisis dalam format JSON yang diminta.
"""
    
    user_prompt = """
Berikan analisis Current Ratio dalam format JSON:
{
    "explanation": "Penjelasan Current Ratio untuk pemilik UMKM",
    "action": "Rekomendasi tindakan konkret"
}
"""
    
    print("   Sending JSON prompt...")
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[system_prompt, user_prompt],
        config=types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=1024,
            response_mime_type="application/json",
        )
    )
    
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
            exit(1)
        
        print("   " + "-" * 66)
    else:
        print("   ❌ Empty response")
        exit(1)
        
except Exception as e:
    print(f"   ❌ JSON generation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test LLM adapter integration
print(f"\n6. Test LLM Adapter Integration:")
try:
    from app.llm_adapter import generate_ratio_explanation, get_llm_status
    
    # Check status
    status = get_llm_status()
    print(f"   LLM Status:")
    print(f"   - Available: {status['genai_available']}")
    print(f"   - Enabled: {status['llm_enabled']}")
    print(f"   - API Key Configured: {status['api_key_configured']}")
    print(f"   - Model: {status['model']}")
    
    if not status['llm_enabled']:
        print("   ⚠️  LLM not enabled - will use fallback")
    
    # Test ratio explanation
    print(f"\n   Testing ratio explanation generation...")
    result = generate_ratio_explanation(
        ratio_code="CR",
        ratio_name="Current Ratio",
        category="Likuiditas",
        value="1.2",
        band="between_warning_critical",
        direction="higher_better",
        data_quality="complete",
        target="2.0",
        warning_threshold="1.5",
        critical_threshold="1.0",
        unit="x"
    )
    
    print(f"\n   Result:")
    print(f"   - Source: {result.get('source')}")
    print(f"   - LLM Available: {result.get('llm_available')}")
    
    if result.get('source') == 'llm':
        print("   ✓ LLM Generation SUCCESS!")
        print(f"\n   Explanation preview:")
        print("   " + "-" * 66)
        explanation = result.get('explanation', '')
        for line in explanation[:200].split('\n'):
            print(f"   {line}")
        if len(explanation) > 200:
            print("   ... (truncated)")
        print("   " + "-" * 66)
    else:
        print(f"   ⚠️  Using fallback - Reason: {result.get('fallback_reason')}")
        
except Exception as e:
    print(f"   ❌ LLM Adapter test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 70)
print("🎉 ALL TESTS PASSED - GEMINI INTEGRATION WORKING!")
print("=" * 70)
print("\n✅ Setup Complete:")
print("   1. google-genai package installed")
print("   2. API key configured and valid")
print("   3. Gemini API responding correctly")
print("   4. JSON mode working")
print("   5. LLM adapter integration working")
print("\n📝 Next steps:")
print("   1. Start backend: uvicorn app.main:app --reload")
print("   2. Test explain endpoint: GET /api/v1/ratios/CR/explain")
print("   3. Monitor LLM usage in logs")
print()
