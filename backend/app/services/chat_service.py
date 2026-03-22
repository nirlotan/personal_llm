# Chat orchestration – LangChain + OpenAI, history management, streaming.
from __future__ import annotations

import time
from typing import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.services.intent_service import augment_prompt
from app.services.session_service import SessionData


def _build_chat_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model="gpt-4o",
        temperature=0.5,
    )


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

    model = _build_chat_model()
    prompt = ChatPromptTemplate.from_messages([
        ("system", session.system_message),
        ("human", "{sentence}"),
    ])
    chain = prompt | model
    response = chain.invoke({"sentence": injected_prompt})

    # Store in session history
    session.langchain_messages.append(HumanMessage(content=injected_prompt))
    session.langchain_messages.append(AIMessage(content=response.content))
    # augmented_chat_messages keeps the full guidance for Firebase; chat_messages is clean for display
    session.augmented_chat_messages.append({"role": "user", "content": injected_prompt})
    session.augmented_chat_messages.append({"role": "assistant", "content": response.content})
    session.chat_messages.append({"role": "assistant", "content": response.content})

    session._injected.add(key)
    return response.content


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
    augmented_prompt, intent_info = augment_prompt(user_content, session)

    # Build the full prompt with history
    model = _build_chat_model()
    prompt = ChatPromptTemplate.from_messages([
        ("system", session.system_message),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{sentence}"),
    ])
    chain = prompt | model

    # Convert stored messages to LangChain format for history
    response = chain.invoke({
        "sentence": augmented_prompt,
        "history": session.langchain_messages,
    })

    # Store in history
    session.langchain_messages.append(HumanMessage(content=augmented_prompt))
    session.langchain_messages.append(AIMessage(content=response.content))
    # augmented_chat_messages keeps the full guidance for Firebase; chat_messages is clean for display
    session.augmented_chat_messages.append({"role": "user", "content": augmented_prompt})
    session.augmented_chat_messages.append({"role": "assistant", "content": response.content})
    session.chat_messages.append({"role": "user", "content": user_content})
    session.chat_messages.append({"role": "assistant", "content": response.content})

    session.last_message_time = time.time()

    return {
        "role": "assistant",
        "content": response.content,
        "intent": intent_info["intent"],
        "topic": intent_info.get("topic"),
    }


def check_can_proceed(session: SessionData, min_messages: int) -> bool:
    """Check if the user has met all conditions to proceed to feedback."""
    msg_count = get_message_count(session)
    all_tasks = all(v == 1 for v in session.chat_status.values())
    return msg_count >= min_messages and all_tasks


def reset_chat_for_next_round(session: SessionData) -> None:
    """Clear chat-related state for the second chat round."""
    if session.chat_type in session.remaining_chat_types:
        session.remaining_chat_types.remove(session.chat_type)
    session.system_message = ""
    session.chat_status = {
        "Friendly Chat": 0,
        "Recommendation": 0,
        "Factual Information Request": 0,
    }
    session.chat_type = None
    session.chat_messages = []
    session.langchain_messages = []
    session.last_message_time = time.time()
    session.messages_timing = []
    session.user_for_the_chat = None
    session.user_embeddings = None
    session.selected_user_similarity = 0.0
    session.recommendation_topics = []
    if hasattr(session, "_injected"):
        session._injected.clear()
