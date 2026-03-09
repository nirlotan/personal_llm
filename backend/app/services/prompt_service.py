# System prompt assembly from templates.
from __future__ import annotations

from pathlib import Path

from app.services.session_service import SessionData

_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def load_template(name: str = "base_message.txt") -> str:
    """Load a system-message template by filename."""
    path = _TEMPLATES_DIR / name
    return path.read_text(encoding="utf-8")


def build_system_prompt(session: SessionData, persona_description: str) -> str:
    """
    Assemble the final system prompt for the chat session.

    Business rules (ported from legacy prepare_prompt.py):
    - vanilla → empty system message
    - All other types → base_message.txt with {character_description} replaced
    """
    chat_type = session.chat_type

    if chat_type == "vanilla":
        session.system_message = ""
        return ""

    template = load_template("base_message.txt")
    final_prompt = template.replace("{character_description}", persona_description)
    session.system_message = final_prompt
    return final_prompt
