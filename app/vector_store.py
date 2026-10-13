
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


def load_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL)


def build_vector_store(chunks, model):
    if not chunks:
        raise ValueError("No text chunks available for indexing.")

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    embeddings = np.asarray(embeddings, dtype=np.float32)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    return index


def search_documents(question, index, chunks, model, top_k=4):
    if index.ntotal == 0:
        return []

    query_embedding = model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    query_embedding = np.asarray(
        query_embedding, dtype=np.float32
    )

    k = min(top_k, index.ntotal)
    scores, indices = index.search(query_embedding, k)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue

        result = dict(chunks[int(idx)])
        result["score"] = float(score)
        results.append(result)

    return results
