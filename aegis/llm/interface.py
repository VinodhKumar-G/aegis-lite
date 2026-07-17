"""
AEGIS Lite — Ollama LLM Interface
Sends prompts to the locally running Ollama server.
No cloud API. No OpenAI key. No data leaves the machine.
"""

import requests
import json
from typing import Optional

from aegis.config import (
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)


def is_ollama_running() -> bool:
    """Check if the Ollama server is running."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def is_model_available() -> bool:
    """Check if the configured model is pulled and ready."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if r.status_code != 200:
            return False
        models = [m["name"] for m in r.json().get("models", [])]
        return any(OLLAMA_MODEL in m for m in models)
    except Exception:
        return False


def ask_llm(prompt: str, model: Optional[str] = None) -> str:
    """
    Send a prompt to the local Ollama LLM and return the response.

    This is the ONLY place where text goes to an AI model.
    It goes to localhost:11434 — your own machine.
    Nothing goes to the internet.

    Args:
        prompt: The full prompt string (including RAG context)
        model: Optional model override

    Returns:
        The model's text response
    """
    if not is_ollama_running():
        return (
            "⚠️ Ollama is not running. "
            "Please run: ollama serve  (in a terminal)"
        )

    target_model = model or OLLAMA_MODEL

    if not is_model_available():
        return (
            f"⚠️ Model '{target_model}' is not available. "
            f"Please run: ollama pull {target_model}"
        )

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": target_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": LLM_MAX_TOKENS,
                },
            },
            timeout=120,  # Local inference can take time on CPU
        )
        response.raise_for_status()
        return response.json()["response"].strip()

    except requests.Timeout:
        return "⚠️ LLM timed out. The model may still be loading — please try again."
    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"