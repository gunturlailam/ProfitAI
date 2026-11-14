"""Test provider LLM (DeepSeek/Gemini/OpenAI).

Fokus: resolusi provider dan pemanggilan DeepSeek. Tidak ada network nyata;
httpx.Client diganti fake. Aturan domain: LLM tidak boleh raise dan selalu
punya jalur fallback.
"""

from app import llm_adapter


# ─── resolve_provider (pure) ──────────────────────────────────────────────────

def test_deepseek_explicit_with_key():
    provider, error = llm_adapter.resolve_provider(
        "deepseek", deepseek_key="sk-x", gemini_key="", openai_key=""
    )
    assert provider == "deepseek"
    assert error is None


def test_deepseek_explicit_without_key_returns_error():
    provider, error = llm_adapter.resolve_provider(
        "deepseek", deepseek_key="", gemini_key="", openai_key=""
    )
    assert provider is None
    assert "DEEPSEEK_API_KEY" in error


def test_deepseek_alias_and_case_insensitive():
    provider, error = llm_adapter.resolve_provider(
        "DeepSeek-Chat", deepseek_key="sk-x", gemini_key="", openai_key=""
    )
    assert provider == "deepseek"
    assert error is None


def test_autodetect_prefers_deepseek_when_multiple_keys():
    provider, error = llm_adapter.resolve_provider(
        "", deepseek_key="sk-d", gemini_key="g", openai_key="o"
    )
    assert provider == "deepseek"
    assert error is None


def test_autodetect_gemini_when_no_deepseek():
    provider, error = llm_adapter.resolve_provider(
        "", deepseek_key="", gemini_key="g", openai_key="o"
    )
    assert provider == "gemini"
    assert error is None


def test_unknown_provider_lists_supported_options():
    provider, error = llm_adapter.resolve_provider(
        "claude", deepseek_key="sk-x", gemini_key="", openai_key=""
    )
    assert provider is None
    assert "deepseek" in error


# ─── _call_deepseek ───────────────────────────────────────────────────────────

def test_call_deepseek_without_key_returns_error(monkeypatch):
    monkeypatch.setattr(llm_adapter, "DEEPSEEK_API_KEY", "")
    text, error = llm_adapter._call_deepseek("sys", "user")
    assert text is None
    assert "DEEPSEEK_API_KEY" in error


def test_call_deepseek_parses_openai_compatible_response(monkeypatch):
    captured = {}

    class _FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "  narasi aman  "}}]}

    class _FakeClient:
        def __init__(self, **kwargs):
            captured["timeout"] = kwargs.get("timeout")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return _FakeResponse()

    monkeypatch.setattr(llm_adapter, "DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setattr(llm_adapter, "DEEPSEEK_MODEL", "deepseek-chat")
    monkeypatch.setattr(llm_adapter.httpx, "Client", _FakeClient)

    text, error = llm_adapter._call_deepseek("SISTEM", "PROMPT")

    assert error is None
    assert text == "narasi aman"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-test"
    assert captured["json"]["model"] == "deepseek-chat"
    assert captured["json"]["messages"][0]["role"] == "system"
    assert captured["json"]["messages"][1]["content"] == "PROMPT"


def test_call_deepseek_empty_choices_returns_error(monkeypatch):
    class _FakeResponse:
        status_code = 200

        def json(self):
            return {"choices": []}

    class _FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers=None, json=None):
            return _FakeResponse()

    monkeypatch.setattr(llm_adapter, "DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setattr(llm_adapter.httpx, "Client", _FakeClient)

    text, error = llm_adapter._call_deepseek("sys", "user")
    assert text is None
    assert "kosong" in error


def test_call_deepseek_http_error_is_handled(monkeypatch):
    class _FakeResponse:
        status_code = 401

        def json(self):
            return {}

    class _FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers=None, json=None):
            return _FakeResponse()

    monkeypatch.setattr(llm_adapter, "DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setattr(llm_adapter, "LLM_MAX_RETRIES", 0)
    monkeypatch.setattr(llm_adapter.httpx, "Client", _FakeClient)

    text, error = llm_adapter._call_deepseek("sys", "user")
    assert text is None
    assert "401" in error
