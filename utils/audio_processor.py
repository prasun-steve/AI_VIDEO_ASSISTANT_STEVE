import yt_dlp
from pydub import AudioSegment
import base64
import os
from pathlib import Path
from uuid import uuid4

DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloades"
DOWNLOAD_DIR.mkdir(exist_ok=True)


def _write_youtube_cookies(run_dir: Path) -> Path | None:
    """Materialize an optional Render secret as a short-lived cookie file."""
    encoded_cookies = os.getenv("YOUTUBE_COOKIES_B64")
    if not encoded_cookies:
        return None

    # Preferred: base64, which is safe to paste as a single Render secret.
    # Also accept a raw Netscape cookie file pasted into an environment value;
    # Render supports multiline secret values and this makes setup less fragile.
    value = encoded_cookies.strip()
    if value.startswith(("# HTTP Cookie File", "# Netscape HTTP Cookie File")):
        cookies = value.replace("\\n", "\n").encode("utf-8")
    else:
        try:
            cookies = base64.b64decode(value, validate=True)
        except Exception as error:
            raise RuntimeError(
                "YOUTUBE_COOKIES_B64 must contain either base64-encoded data "
                "or raw Netscape/Mozilla cookies.txt content."
            ) from error
    if not cookies.startswith((b"# HTTP Cookie File", b"# Netscape HTTP Cookie File")):
        raise RuntimeError(
            "YOUTUBE_COOKIES_B64 must contain a Netscape/Mozilla cookies.txt file."
        )
    cookie_path = run_dir / "youtube-cookies.txt"
    cookie_path.write_bytes(cookies)
    return cookie_path


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

def download_youtube_audio(url :str) ->str:
    run_dir = DOWNLOAD_DIR / uuid4().hex
    run_dir.mkdir()
    output_path = str(run_dir / "audio.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }
    cookie_path = _write_youtube_cookies(run_dir)
    if cookie_path:
        ydl_opts["cookiefile"] = str(cookie_path)
    user_agent = os.getenv("YOUTUBE_USER_AGENT")
    if user_agent:
        ydl_opts["http_headers"] = {"User-Agent": user_agent}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)
    wav_files = list(run_dir.glob("*.wav"))
    if not wav_files:
        raise RuntimeError("YouTube audio download finished but FFmpeg did not create a WAV file. Install FFmpeg and retry.")
    return str(wav_files[0])



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

    # YouTube downloads are stored in their own UUID directory, so this is safe.
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
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        if not os.path.isfile(source):
            raise FileNotFoundError(f"Local file does not exist: {source}")
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks
