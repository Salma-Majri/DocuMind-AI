
def split_documents(documents, chunk_size=1000, overlap=150):
    """
    Split extracted documents into smaller text chunks.
    Preserve source metadata for citations.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size - 1.")

    chunks = []

    for document in documents:
        text = document["text"].strip()

        if not text:
            continue

        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "source": document["source"],
                    "page": document.get("page"),
                })

            if end == len(text):
                break

            start = end - overlap

    return chunks
