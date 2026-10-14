import os
import json
import re

import streamlit as st
from groq import Groq


# ==========================================
# GROQ CLIENT
# ==========================================
def create_groq_client():
    """
    Create a Groq client using the API key
    stored in environment variables or Streamlit secrets.
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            api_key = None

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to your .env file "
            "or Streamlit Cloud secrets."
        )

    return Groq(api_key=api_key)


def get_groq_model():
    """Return the configured Groq model."""
    model = os.getenv("GROQ_MODEL")

    if not model:
        try:
            model = st.secrets.get("GROQ_MODEL")
        except Exception:
            model = None

    return model or "openai/gpt-oss-20b"


# ==========================================
# EXTRACT TEXT FROM RETRIEVED CHUNKS
# ==========================================
def extract_chunk_text(chunk):
    """
    Support chunks represented as strings, dictionaries,
    or document objects.
    """
    if isinstance(chunk, str):
        return chunk

    if isinstance(chunk, dict):
        return (
            chunk.get("page_content")
            or chunk.get("text")
            or chunk.get("content")
            or str(chunk)
        )

    if hasattr(chunk, "page_content"):
        return chunk.page_content

    return str(chunk)


def extract_chunk_source(chunk):
    """Try to retrieve the source filename from a chunk."""
    if isinstance(chunk, dict):
        metadata = chunk.get("metadata", {})
        return (
            metadata.get("source")
            or metadata.get("file_name")
            or metadata.get("filename")
            or "Uploaded document"
        )

    metadata = getattr(chunk, "metadata", {}) or {}

    return (
        metadata.get("source")
        or metadata.get("file_name")
        or metadata.get("filename")
        or "Uploaded document"
    )


# ==========================================
# ANSWER QUESTIONS
# ==========================================
def answer_question(question, retrieved_chunks, client=None):
    """
    Answer a question using retrieved document chunks.

    Returns:
        {
            "answer": "...",
            "sources": [...]
        }
    """
    if not retrieved_chunks:
        return {
            "answer": (
                "I couldn't find relevant information in your "
                "processed documents to answer this question."
            ),
            "sources": [],
        }

    if client is None:
        client = create_groq_client()

    context_parts = []
    sources = []

    for chunk in retrieved_chunks:
        text = extract_chunk_text(chunk)
        source = extract_chunk_source(chunk)

        if text.strip():
            context_parts.append(text)

        if source not in sources:
            sources.append(source)

    context = "\n\n".join(context_parts)

    system_prompt = """
You are DocuMind AI, a document question-answering assistant.

Rules:
- Answer using the provided document context.
- Do not invent facts that are not supported by the context.
- If the answer is not available in the context, say so clearly.
- Be clear, helpful, and well organized.
- Answer in the same language as the user's question when possible.
"""

    user_prompt = f"""
DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

Answer the question based on the document context.
"""

    response = client.chat.completions.create(
        model=get_groq_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content or ""

    return {
        "answer": answer.strip(),
        "sources": sources,
    }


# ==========================================
# PARSE JSON FROM THE MODEL RESPONSE
# ==========================================
def parse_json_response(content):
    """Parse JSON, including JSON wrapped in Markdown fences."""
    if not content:
        raise ValueError("The model returned an empty response.")

    cleaned = content.strip()

    # Remove Markdown code fences if present
    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try extracting a JSON object from surrounding text
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(
        "The model did not return valid JSON. Please generate the QCM again."
    )


# ==========================================
# VALIDATE QCM
# ==========================================
def validate_qcm(data):
    """Validate the generated multiple-choice questions."""
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict):
        questions = data.get("questions", [])
    else:
        questions = []

    if not isinstance(questions, list) or not questions:
        raise ValueError("No questions were generated.")

    validated_questions = []

    for index, item in enumerate(questions):
        if not isinstance(item, dict):
            continue

        question = str(item.get("question", "")).strip()
        options = item.get("options", {})
        correct_answer = str(
            item.get("correct_answer", "")
        ).strip().upper()

        if not isinstance(options, dict):
            continue

        normalized_options = {
            str(key).strip().upper(): str(value).strip()
            for key, value in options.items()
        }

        required_letters = ["A", "B", "C", "D"]

        if not question:
            continue

        if not all(
            letter in normalized_options
            and normalized_options[letter]
            for letter in required_letters
        ):
            continue

        if correct_answer not in required_letters:
            continue

        validated_questions.append(
            {
                "question": question,
                "options": {
                    letter: normalized_options[letter]
                    for letter in required_letters
                },
                "correct_answer": correct_answer,
                "explanation": str(
                    item.get("explanation", "")
                ).strip(),
                "source": str(
                    item.get("source", "")
                ).strip(),
            }
        )

    if not validated_questions:
        raise ValueError(
            "The generated questions were not in the expected format. "
            "Please try generating the QCM again."
        )

    return validated_questions


# ==========================================
# GENERATE QCM
# ==========================================
def generate_qcm(
    chunks,
    number_of_questions=5,
    difficulty="Medium",
    client=None,
):
    """
    Generate a multiple-choice quiz from processed document chunks.

    Args:
        chunks: Processed document chunks.
        number_of_questions: Number of questions requested.
        difficulty: Easy, Medium, or Hard.
        client: Optional Groq client.

    Returns:
        A list of validated question dictionaries.
    """
    if not chunks:
        raise ValueError(
            "Please process at least one document before generating a QCM."
        )

    if client is None:
        client = create_groq_client()

    # Limit context size to avoid sending excessively large prompts
    context_parts = []
    source_names = []

    for chunk in chunks:
        text = extract_chunk_text(chunk)
        source = extract_chunk_source(chunk)

        if text.strip():
            context_parts.append(
                f"Source: {source}\n{text.strip()}"
            )

        if source not in source_names:
            source_names.append(source)

    context = "\n\n".join(context_parts)
    context = context[:45000]

    system_prompt = """
You are an educational quiz generator for DocuMind AI.

Generate multiple-choice questions using ONLY the supplied document context.

Return valid JSON only. Do not include Markdown fences or any extra text.

Use exactly this structure:
{
  "questions": [
    {
      "question": "Question text",
      "options": {
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      },
      "correct_answer": "A",
      "explanation": "Why this answer is correct",
      "source": "Source filename if available"
    }
  ]
}

Requirements:
- Each question must have exactly four options: A, B, C, D.
- Only one option must be correct.
- correct_answer must be one of A, B, C, D.
- Questions and answers must be supported by the supplied context.
- Avoid duplicate questions.
- Do not invent information.
- If the context is insufficient, generate fewer questions rather than inventing facts.
- Keep explanations short and clear.
"""

    user_prompt = f"""
Create a QCM with these settings:

Number of questions requested: {number_of_questions}
Difficulty: {difficulty}

DOCUMENT CONTEXT:
{context}

Generate the questions now as valid JSON.
"""

    response = client.chat.completions.create(
        model=get_groq_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content or ""
    data = parse_json_response(content)
    questions = validate_qcm(data)

    # Return no more than the requested number
    return questions[:number_of_questions]
