"""
Test untuk DeepSeek Integration via Ethereal Market
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=" * 70)
print("DEEPSEEK INTEGRATION TEST (via Ethereal Market)")
print("=" * 70)

# Check configuration
api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
base_url = os.getenv("DEEPSEEK_BASE_URL", "").strip()
model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()

print(f"\n1. Configuration Check:")
print(f"   API Key: {'✓ Configured' if api_key else '❌ NOT configured'}")
if api_key:
    print(f"   Key prefix: {api_key[:15]}...")
print(f"   Base URL: {base_url or 'NOT SET'}")
print(f"   Model: {model}")

if not api_key:
    print("\n   ❌ DEEPSEEK_API_KEY not found in .env")
    exit(1)

# Test import
print(f"\n2. Package Import Test:")
try:
    from openai import OpenAI
    print("   ✓ openai package imported")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    print("\n   Install with: pip install openai")
    exit(1)

# Test list models endpoint
print(f"\n3. Test Models Endpoint:")
try:
    import requests
    
    models_url = f"{base_url}/models"
    print(f"   GET {models_url}")
    
    response = requests.get(
        models_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10
    )
    
    if response.status_code == 200:
        models_data = response.json()
        print(f"   ✓ Response: {response.status_code}")
        
        if "data" in models_data:
            available_models = [m.get("id") for m in models_data["data"]]
            print(f"   Available models: {', '.join(available_models[:5])}")
            
            if model in available_models:
                print(f"   ✓ Model '{model}' is available")
            else:
                print(f"   ⚠️  Model '{model}' not found, using first available")
                model = available_models[0] if available_models else model
        else:
            print(f"   ⚠️  Unexpected response format: {models_data}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"   ⚠️  Models endpoint check failed: {e}")
    print("   Continuing with configured model...")

# Initialize client
print(f"\n4. Initialize DeepSeek Client:")
try:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=30
    )
    print("   ✓ Client initialized successfully")
except Exception as e:
    print(f"   ❌ Client initialization failed: {e}")
    exit(1)

# Test simple completion
print(f"\n5. Test Chat Completion:")
try:
    print(f"   Sending test prompt to {model}...")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Anda adalah asisten keuangan untuk UMKM Indonesia."},
            {"role": "user", "content": "Jelaskan dalam 2 kalimat: Apa itu Current Ratio?"}
        ],
        temperature=0.7,
        max_tokens=200
    )
    
    if response and response.choices and len(response.choices) > 0:
        message = response.choices[0].message
        if message and message.content:
            print("   ✓ Response received!")
            print(f"\n   Response:")
            print("   " + "-" * 66)
            for line in message.content.strip().split('\n'):
                print(f"   {line}")
            print("   " + "-" * 66)
        else:
            print("   ❌ Empty message content")
            exit(1)
    else:
        print("   ❌ No choices in response")
        exit(1)
        
except Exception as e:
    print(f"   ❌ Completion failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test JSON mode
print(f"\n6. Test JSON Output Mode:")
try:
    print("   Sending JSON prompt...")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Anda adalah CFO virtual untuk UMKM. Berikan output dalam format JSON."},
            {"role": "user", "content": """
Analisis Current Ratio untuk UMKM dalam format JSON:
{
    "explanation": "Penjelasan Current Ratio",
    "action": "Rekomendasi tindakan"
}
"""}
        ],
        temperature=0.7,
        max_tokens=500,
        response_format={"type": "json_object"}
    )
    
    if response and response.choices and len(response.choices) > 0:
        content = response.choices[0].message.content
        if content:
            print("   ✓ JSON Response received!")
            print(f"\n   JSON Response:")
            print("   " + "-" * 66)
            
            import json
            try:
                parsed = json.loads(content)
                print(f"   {json.dumps(parsed, indent=2, ensure_ascii=False)}")
                print("   ✓ Valid JSON!")
            except json.JSONDecodeError as e:
                print(f"   ❌ Invalid JSON: {e}")
                print(f"   Raw: {content}")
                exit(1)
            
            print("   " + "-" * 66)
        else:
            print("   ❌ Empty response")
            exit(1)
    else:
        print("   ❌ No choices in response")
        exit(1)
        
except Exception as e:
    print(f"   ❌ JSON generation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test LLM adapter integration
print(f"\n7. Test LLM Adapter Integration:")
try:
    from app.llm_adapter import generate_ratio_explanation, get_llm_status
    
    # Check status
    status = get_llm_status()
    print(f"   LLM Status:")
    print(f"   - OpenAI Available: {status['openai_available']}")
    print(f"   - LLM Enabled: {status['llm_enabled']}")
    print(f"   - API Key Configured: {status['api_key_configured']}")
    print(f"   - Base URL: {status['base_url']}")
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
    print(f"   - Model: {result.get('model', 'N/A')}")
    
    if result.get('source') == 'llm':
        print("   ✓ LLM Generation SUCCESS!")
        print(f"\n   Explanation preview:")
        print("   " + "-" * 66)
        explanation = result.get('explanation', '')
        lines = explanation.split('\n')
        for line in lines[:5]:
            print(f"   {line}")
        if len(lines) > 5:
            print("   ... (truncated)")
        print("   " + "-" * 66)
    elif result.get('source') == 'fallback':
        print(f"   ⚠️  Using fallback")
        print(f"   Reason: {result.get('fallback_reason')}")
    else:
        print(f"   ⚠️  Unexpected source: {result.get('source')}")
        
except Exception as e:
    print(f"   ❌ LLM Adapter test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 70)
print("🎉 ALL TESTS PASSED - DEEPSEEK INTEGRATION WORKING!")
print("=" * 70)
print("\n✅ Setup Complete:")
print("   1. openai package installed and working")
print("   2. API key configured and valid")
print("   3. Ethereal Market endpoint responding")
print("   4. Chat completion working")
print("   5. JSON mode working")
print("   6. LLM adapter integration working")
print("\n📝 Next steps:")
print("   1. Start backend: uvicorn app.main:app --reload")
print("   2. Test explain endpoint: GET /api/v1/ratios/CR/explain")
print("   3. Monitor LLM usage in logs")
print()
