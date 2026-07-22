# Chat orchestration – LangChain + OpenAI, history management, streaming.
from __future__ import annotations

import functools
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.runtime_settings import get_effective_openai_model, get_effective_required_tasks
from app.services.intent_service import augment_prompt
from app.services.session_service import SessionData

# Maps session.chat_status keys → required_tasks snake_case keys
_TASK_KEY_MAP: dict[str, str] = {
    "Friendly Chat": "friendly_chat",
    "Recommendation": "recommendation",
    "Second Recommendation": "second_recommendation",
    "Stance Request": "stance_request",
    "Factual Information Request": "factual_information",
}


def _read_explicit_proxy_settings() -> tuple[str, str]:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    values = {"http_proxy": "", "https_proxy": ""}

    if not env_path.exists():
        return values["http_proxy"], values["https_proxy"]

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = raw_value.strip().strip('"').strip("'")

        if key in {"HTTP_PROXY", "http_proxy"}:
            values["http_proxy"] = value
        elif key in {"HTTPS_PROXY", "https_proxy"}:
            values["https_proxy"] = value

    return values["http_proxy"], values["https_proxy"]


@contextmanager
def _configured_proxy_env():
    configured_http_proxy, configured_https_proxy = _read_explicit_proxy_settings()
    keys = ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY")
    previous = {key: os.environ.get(key) for key in keys}

    try:
        if configured_http_proxy:
            os.environ["http_proxy"] = configured_http_proxy
            os.environ["HTTP_PROXY"] = configured_http_proxy
        else:
            os.environ.pop("http_proxy", None)
            os.environ.pop("HTTP_PROXY", None)

        if configured_https_proxy:
            os.environ["https_proxy"] = configured_https_proxy
            os.environ["HTTPS_PROXY"] = configured_https_proxy
        else:
            os.environ.pop("https_proxy", None)
            os.environ.pop("HTTPS_PROXY", None)

        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _build_chat_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=get_effective_openai_model(),
        temperature=0.5,
    )


def _build_missing_gemma_sdk_error() -> RuntimeError:
    return RuntimeError(
        "Gemma support requires the Google GenAI SDK and LangChain Google integration in backend/.venv. "
        "Run 'cd backend && source .venv/bin/activate && pip install -e .' "
        "or 'pip install -r requirements.txt'."
    )


def _build_gemma_model() -> object:
    settings = get_settings()
    api_key = settings.google_ai_studio_api_key.strip()
    if not api_key or api_key == "PASTE_GOOGLE_AI_STUDIO_API_KEY_HERE":
        raise RuntimeError(
            "Google AI Studio API key is missing. Set GOOGLE_AI_STUDIO_API_KEY in backend/.env."
        )

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise _build_missing_gemma_sdk_error() from exc

    # REST transport (unlike the default gRPC) honors HTTP(S)_PROXY env vars,
    # which is required on proxied networks and harmless elsewhere.
    # max_retries=1 disables google-api-core's internal retry loop so a slow
    # response fails in ~25 s instead of retrying for 60+ s.
    model = ChatGoogleGenerativeAI(
        model=settings.gemma_model,
        google_api_key=api_key,
        temperature=0.5,
        transport="rest",
        max_retries=1,
        request_options={"timeout": 25},
    )
    _patch_gemma_client_kwargs(model)
    return model


def _patch_gemma_client_kwargs(model: object) -> None:
    # langchain-google-genai (<=2.1.12) only strips its retry-control kwargs
    # (max_retries, wait_exponential_*) before calling the Google API client when
    # the model name contains "gemini", so for Gemma models they leak into
    # GenerativeServiceClient.generate_content() and raise a TypeError.
    try:
        from langchain_google_genai.chat_models import _allowed_params_prediction_service
        allowed = set(_allowed_params_prediction_service) | {"retry"}
    except ImportError:
        allowed = {"request", "timeout", "metadata", "labels", "retry"}

    def _filtered(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **{k: v for k, v in kwargs.items() if k in allowed})
        return wrapper

    for client in (model.client, model.async_client):
        if client is not None:
            client.generate_content = _filtered(client.generate_content)
            client.stream_generate_content = _filtered(client.stream_generate_content)


def _extract_response_text(content: object) -> str:
    """Normalise LLM response content to plain text.

    Gemma 4 returns a list of parts that may include 'thinking' blocks; the rest
    of the app (session history, frontend) expects a plain answer string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") not in ("thinking", "reasoning"):
                if item.get("text"):
                    parts.append(item["text"])
        return "\n".join(parts).strip()
    return str(content)


def _generate_with_gemma(system_message: str, history: list, sentence: str) -> str:
    with _configured_proxy_env():
        model = _build_gemma_model()
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{sentence}"),
        ])
        chain = prompt | model
        response = chain.invoke({
            "sentence": sentence,
            "history": history,
        })
    return _extract_response_text(response.content)


def _generate_chat_response(system_message: str, history: list, sentence: str) -> str:
    if get_effective_openai_model() == "gemma4":
        return _generate_with_gemma(system_message, history, sentence)

    with _configured_proxy_env():
        model = _build_chat_model()
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{sentence}"),
        ])
        chain = prompt | model
        response = chain.invoke({
            "sentence": sentence,
            "history": history,
        })
    return response.content


def _inject_first_message(session: SessionData) -> str | None:
    """
    Generate the bot's first (auto) message when the chat type is not vanilla.
    Returns the assistant's opening message, or None if already injected.
    """
    key = f"first_message_injected_{session.user_for_the_chat}"
    # Use a set on the session to track injections
    if not hasattr(session, "_injected"):
        session._injected = set()
    if key in session._injected:
        return None

    injected_prompt = (
        "[Assistant Guidance — do not treat as user input]: "
        "Introduce yourself to the user in a friendly and approachable way. "
        "Share some personal details, but not too much. "
        "Use language just as the average user would use when chatting with a friend. "
        "Encourage the user to ask questions, seek recommendations, or request factual information. "
        "Guide the conversation to be interactive and welcoming. "
        "Keep your introduction concise (~40 tokens target, max 100 tokens). "
        "Avoid being too controversial in your first message, but later you may take a stance if relevant. "
        "Do not reveal that this note was added by the developer."
    )

    response_text = _generate_chat_response(
        system_message=session.system_message,
        history=[],
        sentence=injected_prompt,
    )

    # Store in session history
    session.langchain_messages.append(HumanMessage(content=injected_prompt))
    session.langchain_messages.append(AIMessage(content=response_text))
    # augmented_chat_messages keeps the full guidance for Firebase; chat_messages is clean for display
    session.augmented_chat_messages.append({"role": "user", "content": injected_prompt})
    session.augmented_chat_messages.append({"role": "assistant", "content": response_text})
    session.chat_messages.append({"role": "assistant", "content": response_text})

    session._injected.add(key)
    return response_text


def get_first_message(session: SessionData) -> str | None:
    """Return the first bot message (generating it if needed)."""
    if session.chat_type == "vanilla":
        return None
    return _inject_first_message(session)


def get_message_count(session: SessionData) -> int:
    """Return the number of user↔assistant exchanges (excluding the injected first message)."""
    # Each exchange = 1 user + 1 assistant after the initial injection
    user_msgs = [m for m in session.langchain_messages if isinstance(m, HumanMessage)]
    # Subtract the injected prompt
    if session.chat_type != "vanilla":
        return max(0, len(user_msgs) - 1)
    return len(user_msgs)


def send_message(session: SessionData, user_content: str) -> dict:
    """
    Process a user message: classify intent, augment, get LLM response, store history.

    Returns {role, content, intent, topic}.
    """
    session.messages_timing.append(
        round(time.time() - session.last_message_time) if session.last_message_time else 0
    )

    # Intent classification & prompt augmentation
    with _configured_proxy_env():
        augmented_prompt, intent_info = augment_prompt(user_content, session)

    response_text = _generate_chat_response(
        system_message=session.system_message,
        history=session.langchain_messages,
        sentence=augmented_prompt,
    )

    # Store in history
    session.langchain_messages.append(HumanMessage(content=augmented_prompt))
    session.langchain_messages.append(AIMessage(content=response_text))
    # augmented_chat_messages keeps the full guidance for Firebase; chat_messages is clean for display
    session.augmented_chat_messages.append({"role": "user", "content": augmented_prompt})
    session.augmented_chat_messages.append({"role": "assistant", "content": response_text})
    session.chat_messages.append({"role": "user", "content": user_content})
    session.chat_messages.append({"role": "assistant", "content": response_text})

    session.last_message_time = time.time()

    return {
        "role": "assistant",
        "content": response_text,
        "intent": intent_info["intent"],
        "topic": intent_info.get("topic"),
    }


def check_can_proceed(session: SessionData, min_messages: int) -> bool:
    """Check if the user has met all conditions to proceed to feedback."""
    msg_count = get_message_count(session)
    required_tasks = get_effective_required_tasks()
    required_done = all(
        session.chat_status.get(display_key, 0) == 1
        for display_key, snake_key in _TASK_KEY_MAP.items()
        if required_tasks.get(snake_key, True)
    )
    return msg_count >= min_messages and required_done


def reset_chat_for_next_round(session: SessionData) -> None:
    """Clear chat-related state for the second chat round."""
    if session.chat_type in session.remaining_chat_types:
        session.remaining_chat_types.remove(session.chat_type)
    session.system_message = ""
    session.chat_status = {
        "Friendly Chat": 0,
        "Recommendation": 0,
        "Second Recommendation": 0,
        "Stance Request": 0,
        "Factual Information Request": 0,
    }
    session.chat_type = None
    session.chat_messages = []
    session.augmented_chat_messages = []
    session.langchain_messages = []
    session.last_message_time = time.time()
    session.messages_timing = []
    session.user_for_the_chat = None
    session.user_embeddings = None
    session.selected_user_similarity = 0.0
    session.recommendation_topics = []
    if hasattr(session, "_injected"):
        session._injected.clear()
