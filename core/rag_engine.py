"""Meeting Q&A using lexical context selection plus Groq-hosted generation."""
from __future__ import annotations
from dataclasses import dataclass
from langchain_core.prompts import ChatPromptTemplate
from core.llm import get_llm
from core.runtime import invoke_with_retry
from core.vector_store import MeetingSearch, build_vector_store

@dataclass
class MeetingRagChain:
    search: MeetingSearch
    def invoke(self, question: str) -> str:
        context = "\n\n".join(self.search.search(question))
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert meeting assistant. Answer only from the meeting-transcript excerpts below. If the answer is not in the excerpts, say: I could not find this information in the meeting transcript.\n\nMeeting transcript excerpts:\n{context}"""),
            ("human", "{question}"),
        ])
        return get_llm(temperature=0.2).invoke(prompt.invoke({"context": context, "question": question}))

def build_rag_chain(transcript: str) -> MeetingRagChain:
    return MeetingRagChain(build_vector_store(transcript))

def ask_question(rag_chain: MeetingRagChain, question: str) -> str:
    return invoke_with_retry(lambda: rag_chain.invoke(question), "Groq question answering")
