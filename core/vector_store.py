"""In-memory lexical retrieval with no embedding model download or inference."""
from __future__ import annotations
import re
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter

def _terms(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9']+", text.lower()))

@dataclass
class MeetingSearch:
    chunks: list[str]
    def search(self, question: str, k: int = 4) -> list[str]:
        query_terms = _terms(question)
        ranked = sorted(enumerate(self.chunks), key=lambda item: (len(query_terms & _terms(item[1])), -item[0]), reverse=True)
        return [chunk for _, chunk in ranked[:k]]

def build_vector_store(transcript: str) -> MeetingSearch:
    chunks = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150).split_text(transcript)
    if not chunks:
        raise ValueError("Cannot build meeting search because the transcript is empty.")
    return MeetingSearch(chunks)

def load_vector_store():
    raise RuntimeError("Saved vector stores are not used; analyse a meeting first.")
