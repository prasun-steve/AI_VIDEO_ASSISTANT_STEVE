"""Hosted speech-to-text via Groq; no speech model is loaded on this server."""
from __future__ import annotations
import os
from pathlib import Path
from groq import Groq
from core.runtime import invoke_with_retry

DEFAULT_STT_MODEL = "whisper-large-v3-turbo"

def _client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to .env locally or to your host's secret settings.")
    return Groq(api_key=api_key)

def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """Transcribe one generated WAV chunk with Groq's hosted Whisper model."""
    path = Path(chunk_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio chunk was not found: {chunk_path}")
    language_code = "en" if language.lower() == "english" else None
    model = os.getenv("GROQ_STT_MODEL", DEFAULT_STT_MODEL)
    def request_transcription() -> str:
        with path.open("rb") as audio_file:
            response = _client().audio.transcriptions.create(
                file=(path.name, audio_file.read()), model=model,
                response_format="json", temperature=0,
                **({"language": language_code} if language_code else {}),
            )
        return (response.text or "").strip()
    return invoke_with_retry(request_transcription, "Groq transcription")

def transcribe_all(chunks: list[str], language: str = "english") -> str:
    print(f"Using Groq {os.getenv('GROQ_STT_MODEL', DEFAULT_STT_MODEL)} for transcription.")
    parts = []
    for index, chunk in enumerate(chunks, start=1):
        print(f"Transcribing chunk {index}/{len(chunks)}...")
        text = transcribe_chunk(chunk, language=language)
        if text:
            parts.append(text)
    print("Transcription complete.")
    return " ".join(parts)
