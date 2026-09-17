from pydub import AudioSegment
import os
from pathlib import Path
from uuid import uuid4

DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloades"
DOWNLOAD_DIR.mkdir(exist_ok=True)


def save_uploaded_file(uploaded_file) -> str:
    """Save a Streamlit upload in an isolated temporary run directory.

    A deployed service cannot access a visitor's local filesystem.  Keeping the
    upload beside the generated chunks also lets ``cleanup_audio_files`` remove
    every temporary file after the request finishes.
    """
    run_dir = DOWNLOAD_DIR / uuid4().hex
    run_dir.mkdir()
    safe_name = Path(uploaded_file.name).name or "upload"
    destination = run_dir / safe_name
    destination.write_bytes(uploaded_file.getvalue())
    return str(destination)

def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #16khz
    audio.export(output_path, format="wav")
    return output_path



def chunk_audio(wav_path : str , chunk_minutes : int = 10) -> list:
    # 16 kHz mono WAV is about 19.2 MB for ten minutes.  This stays under
    # Groq's 25 MB free-tier transcription request limit without any model
    # running on the host.
    audio = AudioSegment.from_wav(wav_path).set_channels(1).set_frame_rate(16000)
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []

    for i, start in enumerate(range(0,len(audio),chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path , format = "wav")

        chunks.append(chunk_path)
    
    return chunks


def cleanup_audio_files(chunks: list[str]) -> None:
    """Delete only generated audio for a completed/failed run."""
    if not chunks:
        return
    for chunk in chunks:
        try:
            Path(chunk).unlink(missing_ok=True)
        except OSError as error:
            print(f"Could not remove temporary chunk {chunk}: {error}")

    # Uploads are stored in their own UUID directory, so this is safe.
    parent = Path(chunks[0]).parent
    try:
        if parent.parent == DOWNLOAD_DIR:
            for file in parent.iterdir():
                file.unlink(missing_ok=True)
            parent.rmdir()
    except OSError as error:
        print(f"Could not remove temporary download directory: {error}")


def cleanup_temporary_source(source_path: str | None) -> None:
    """Remove an uploaded temporary source when processing fails before chunks exist."""
    if not source_path:
        return
    parent = Path(source_path).parent
    if parent.parent != DOWNLOAD_DIR:
        return
    try:
        for file in parent.iterdir():
            file.unlink(missing_ok=True)
        parent.rmdir()
    except OSError as error:
        print(f"Could not remove temporary upload directory: {error}")

def process_input(source: str) -> list:
    if not os.path.isfile(source):
        raise FileNotFoundError(f"Uploaded file does not exist: {source}")
    print("Processing uploaded media...")
    wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks
