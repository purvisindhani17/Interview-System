"""
Voice I/O abstraction: Text-to-Speech and Speech-to-Text.

Same principle as llm_client.py: every module that needs to speak a
question or transcribe an answer imports from here, never from the
OpenAI SDK directly. Swapping TTS to ElevenLabs (as the spec allows) or
swapping STT to a self-hosted Whisper model later is a one-file change.
"""

import os

from app.config import settings
from app.utils.llm_client import get_openai_client


class VoiceError(Exception):
    """Raised when speech synthesis or transcription fails."""


def synthesize_speech(text: str, output_path: str) -> str:
    """Convert text to speech audio and save it to output_path (mp3).

    Returns the path the audio was written to.
    """
    if settings.TTS_PROVIDER != "openai":
        raise NotImplementedError(
            f"TTS provider '{settings.TTS_PROVIDER}' is not implemented yet. "
            "Add a branch here when swapping to ElevenLabs or another provider."
        )

    client = get_openai_client()
    try:
        response = client.audio.speech.create(
            model=settings.TTS_MODEL,
            voice=settings.TTS_VOICE,
            input=text,
        )
    except Exception as e:
        raise VoiceError(f"Text-to-speech synthesis failed: {e}") from e

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    response.write_to_file(output_path)
    return output_path


def transcribe_audio(filepath: str) -> str:
    """Transcribe a candidate's spoken-answer audio file to text via Whisper."""
    client = get_openai_client()
    try:
        with open(filepath, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=settings.STT_MODEL,
                file=audio_file,
            )
    except Exception as e:
        raise VoiceError(f"Speech-to-text transcription failed: {e}") from e

    return transcript.text.strip()


def transcribe_with_word_timestamps(filepath: str) -> list[dict]:
    """Transcribe an audio file and return word-level timing data for speech
    pace/pause analysis (Module 7). Returns a list of
    {"word": str, "start": float, "end": float} dicts in chronological order.

    Kept as a separate call from transcribe_audio (used by Module 5) rather
    than requesting word timestamps everywhere by default -- Module 5 only
    needs the quick text transcript to keep the live interview loop
    responsive, while Module 7's pause/pace analysis genuinely needs the
    timing detail. This does mean a second Whisper call per answer if both
    modules run on the same audio; a future optimization could have
    Module 5 request word timestamps once and hand them off, but keeping
    the modules decoupled means Module 7 can also analyze any audio file
    independently of whether it came through a live Module 5 session.
    """
    client = get_openai_client()
    try:
        with open(filepath, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=settings.STT_MODEL,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
    except Exception as e:
        raise VoiceError(f"Word-timestamped transcription failed: {e}") from e

    words = getattr(transcript, "words", None) or []
    return [{"word": w.word, "start": w.start, "end": w.end} for w in words]
