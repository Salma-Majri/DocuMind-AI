
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def create_groq_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    return Groq(api_key=api_key)


def answer_question(question, retrieved_chunks, client=None):
    if not retrieved_chunks:
        return {
            "answer": (
                "I couldn't find relevant information "
                "in the uploaded documents."
            ),
            "sources": [],
        }

    if client is None:
        client = create_groq_client()

    model_name = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    )

    context_parts = []
    sources = []

    for chunk in retrieved_chunks:
        source = chunk.get("source", "Unknown document")
        page = chunk.get("page")

        source_label = source
        if page is not None:
            source_label += f", page {page}"

        context_parts.append(
            f"[Source: {source_label}]\n{chunk['text']}"
        )

        if source_label not in sources:
            sources.append(source_label)

    context = "\n\n---\n\n".join(context_parts)

    system_prompt = """
You are DocuMind AI, an intelligent document assistant.

Answer the user's question using only the supplied context.
If the context does not contain the answer, say so clearly.
Do not invent facts or pretend that unsupported information
appears in the documents.
Answer in the same language as the user's question.
Be clear, helpful, and well organized.
Mention relevant source documents when appropriate.
"""

    user_prompt = f"""
DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

Answer based only on the document context above.
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer or "No answer was generated.",
        "sources": sources,
    }
