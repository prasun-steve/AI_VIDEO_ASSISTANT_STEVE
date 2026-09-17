# AI Video Assistant

This Streamlit app downloads YouTube audio, transcribes it, produces meeting analysis, and supports transcript Q&A.

All AI inference is hosted by Groq: `whisper-large-v3-turbo` for multilingual speech-to-text and `openai/gpt-oss-20b` for text generation. Retrieval uses in-memory keyword matching, so it downloads no embedding model. The host does not install Whisper, PyTorch, Sentence Transformers, or Chroma.

## Local run

1. Copy `.env.example` to `.env` and enter your real `GROQ_API_KEY`.
2. Install FFmpeg, then create and use a project virtual environment:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```

   On Windows you can later double-click `run_local.bat` from the project
   folder to start the same project environment.

## Streamlit Community Cloud

Push the project to GitHub without `.env`, create an app using `app.py`, and add this secret in **Advanced settings → Secrets**:

```toml
GROQ_API_KEY = "your-real-key"
```

`packages.txt` installs FFmpeg and `requirements.txt` contains only lightweight runtime packages.
The app accepts a YouTube URL or a browser upload; a deployed app cannot read a
file path on your own computer. Uploads and generated audio are deleted after
each run.

## Render

Push the project to GitHub, create a Render **Web Service**, choose the repository Dockerfile runtime, then add `GROQ_API_KEY` as a secret environment variable. The Docker image installs FFmpeg but no local AI models; Render's `PORT` is used automatically.

### YouTube links on Render

YouTube may challenge a shared cloud-server IP as a bot. This is controlled by
YouTube, not by Groq, FFmpeg, or Render. The reliable public deployment flow is
to use the **file upload** option instead of a YouTube URL.

For a private college demo, the app can optionally use your own YouTube session
cookies. Export a fresh `cookies.txt` in Netscape/Mozilla format, base64-encode
the entire file as one line, and save it in Render as the secret
`YOUTUBE_COOKIES_B64`. You may also set `YOUTUBE_USER_AGENT` to the matching
browser User-Agent. Never commit cookies, place them in a public repository, or
expose this deployment publicly while they are configured: cookies are account
credentials, expire, and YouTube can still reject a cloud IP.

## Usage note

Hosted Groq models avoid server model downloads, but free API use is rate-limited
and can change; it is not unlimited. The default `whisper-large-v3-turbo` is the
least-cost Groq Whisper option, but it is a paid API model outside any free
allowance. Check your Groq console for the current allowance before opening this
publicly to many users. Each audio chunk is normalized to 16 kHz mono and kept
to ten minutes, staying below Groq's 25 MB free-tier request limit.
