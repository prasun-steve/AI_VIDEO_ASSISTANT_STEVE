"""Groq-backed LangChain adapter. All text generation is hosted by Groq."""
from __future__ import annotations
import os
from groq import Groq
from langchain_core.runnables import RunnableLambda

# Llama 3.1 8B is now an Enterprise-only Groq model.  GPT-OSS 20B is listed
# by this project's Groq account and is suitable for meeting analysis/Q&A.
DEFAULT_MODEL = "openai/gpt-oss-20b"

def _to_messages(prompt_value) -> list[dict[str, str]]:
    role_map = {"human": "user", "ai": "assistant", "system": "system"}
    return [{"role": role_map.get(message.type, "user"), "content": message.content if isinstance(message.content, str) else str(message.content)} for message in prompt_value.to_messages()]

def get_llm(temperature: float = 0.2):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to .env or your deployment secrets.")
    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "1600"))
    def generate(prompt_value) -> str:
        response = client.chat.completions.create(model=model, messages=_to_messages(prompt_value), temperature=temperature, max_completion_tokens=max_tokens)
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Groq returned an empty response. Try again or increase GROQ_MAX_TOKENS.")
        return content.strip()
    return RunnableLambda(generate)
