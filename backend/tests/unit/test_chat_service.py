from __future__ import annotations

import builtins
import os
import types

import pytest

from app.services import chat_service


def test_generate_with_gemma_raises_clear_error_when_google_sdk_missing(monkeypatch):
    monkeypatch.setattr(
        "app.services.chat_service.get_settings",
        lambda: types.SimpleNamespace(
            google_ai_studio_api_key="test-key",
            gemma_model="gemma-3-27b-it",
        ),
    )

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "langchain_google_genai":
            raise ImportError("missing langchain_google_genai")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="Gemma support requires the Google GenAI SDK"):
        chat_service._generate_with_gemma("system", [], "hello")


def test_generate_with_gemma_uses_langchain_prompt_chain(monkeypatch):
    monkeypatch.setattr(
        "app.services.chat_service.get_settings",
        lambda: types.SimpleNamespace(
            google_ai_studio_api_key="test-key",
            gemma_model="gemma-3-27b-it",
        ),
    )

    captured = {}

    class FakeGemmaModel:
        pass

    class FakeChain:
        def invoke(self, payload):
            captured["payload"] = payload
            return types.SimpleNamespace(content="Gemma via LangChain")

    class FakePrompt:
        def __or__(self, model):
            captured["model"] = model
            return FakeChain()

    monkeypatch.setattr(
        "app.services.chat_service._build_gemma_model",
        lambda: FakeGemmaModel(),
    )
    monkeypatch.setattr(
        "app.services.chat_service.ChatPromptTemplate.from_messages",
        lambda messages: FakePrompt(),
    )

    result = chat_service._generate_with_gemma("system text", [], "hello")

    assert result == "Gemma via LangChain"
    assert captured["payload"]["sentence"] == "hello"
    assert captured["payload"]["history"] == []


def test_generate_chat_response_non_gemma_uses_openai_path(monkeypatch):
    monkeypatch.setattr("app.services.chat_service.get_effective_openai_model", lambda: "gpt-5.4-mini")

    called = {"gemma": False, "openai": False}

    def fake_gemma(*args, **kwargs):
        called["gemma"] = True
        return "should-not-be-used"

    class FakeChain:
        def invoke(self, payload):
            called["openai"] = True
            return types.SimpleNamespace(content="OpenAI path")

    class FakePrompt:
        def __or__(self, model):
            return FakeChain()

    monkeypatch.setattr("app.services.chat_service._generate_with_gemma", fake_gemma)
    monkeypatch.setattr(
        "app.services.chat_service.ChatPromptTemplate.from_messages",
        lambda messages: FakePrompt(),
    )
    monkeypatch.setattr("app.services.chat_service._build_chat_model", lambda: object())

    result = chat_service._generate_chat_response("system", [], "hi")

    assert result == "OpenAI path"
    assert called["openai"] is True
    assert called["gemma"] is False


def test_configured_proxy_env_clears_inherited_proxies_when_settings_empty(monkeypatch):
    monkeypatch.setenv("http_proxy", "http://bad-proxy:1")
    monkeypatch.setenv("https_proxy", "http://bad-proxy:2")
    monkeypatch.setenv("HTTP_PROXY", "http://bad-proxy:3")
    monkeypatch.setenv("HTTPS_PROXY", "http://bad-proxy:4")

    monkeypatch.setattr("app.services.chat_service._read_explicit_proxy_settings", lambda: ("", ""))

    with chat_service._configured_proxy_env():
        assert os.environ.get("http_proxy") is None
        assert os.environ.get("https_proxy") is None
        assert os.environ.get("HTTP_PROXY") is None
        assert os.environ.get("HTTPS_PROXY") is None

    assert os.environ.get("http_proxy") == "http://bad-proxy:1"
    assert os.environ.get("https_proxy") == "http://bad-proxy:2"
    assert os.environ.get("HTTP_PROXY") == "http://bad-proxy:3"
    assert os.environ.get("HTTPS_PROXY") == "http://bad-proxy:4"


def test_configured_proxy_env_applies_explicit_proxy_settings(monkeypatch):
    monkeypatch.delenv("http_proxy", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)
    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)

    monkeypatch.setattr(
        "app.services.chat_service._read_explicit_proxy_settings",
        lambda: ("http://configured-proxy:911", "http://configured-secure-proxy:912"),
    )

    with chat_service._configured_proxy_env():
        assert os.environ.get("http_proxy") == "http://configured-proxy:911"
        assert os.environ.get("HTTP_PROXY") == "http://configured-proxy:911"
        assert os.environ.get("https_proxy") == "http://configured-secure-proxy:912"
        assert os.environ.get("HTTPS_PROXY") == "http://configured-secure-proxy:912"

