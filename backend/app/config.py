"""
Central configuration for the AI Interview System backend.

Keeping all environment/config reads in one place makes it trivial to
swap the LLM provider later (OpenAI -> Anthropic -> local model, etc.)
without touching business logic anywhere else in the codebase.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- LLM Provider ---
    # "openai" is the default. To swap providers later, add a new client
    # implementation in app/utils/llm_client.py and change this value.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL") or None

    # --- Voice (TTS / STT) ---
    # TTS_PROVIDER "openai" uses OpenAI's TTS endpoint by default per the
    # spec's "ElevenLabs or any open-source alternative" -- swapping to
    # ElevenLabs later only requires a new branch in voice_client.py.
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "openai")
    TTS_MODEL: str = os.getenv("TTS_MODEL", "tts-1")
    TTS_VOICE: str = os.getenv("TTS_VOICE", "alloy")
    STT_MODEL: str = os.getenv("STT_MODEL", "whisper-1")

    # --- Storage ---
    # SQLite/JSON toggle isn't needed yet for Module 1 (no DB writes),
    # but we define the path now so later modules share one convention.
    DATA_DIR: str = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
    RESUME_UPLOAD_DIR: str = os.path.join(DATA_DIR, "resumes")
    STORAGE_DIR: str = os.path.join(DATA_DIR, "storage")
    AUDIO_DIR: str = os.path.join(DATA_DIR, "audio")

    # --- Upload limits ---
    MAX_RESUME_SIZE_MB: int = int(os.getenv("MAX_RESUME_SIZE_MB", "10"))


settings = Settings()

# Ensure required directories exist at import time.
os.makedirs(settings.RESUME_UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.AUDIO_DIR, exist_ok=True)
