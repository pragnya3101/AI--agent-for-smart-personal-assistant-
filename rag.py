"""
rag.py
Retrieval-Augmented Generation over the user's own documents
(notes, PDFs, txt files placed in ./knowledge_base/).
Uses sentence-transformers for embeddings and numpy cosine
similarity for retrieval (no external vector DB needed).
"""

import os
import glob
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

KB_DIR = "knowledge_base"
INDEX_PATH = "rag_index.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _read_file(path):
    if path.lower().endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return [c.strip() for c in chunks if c.strip()]


def build_index():
    """Scan KB_DIR, chunk + embed everything, save index to disk."""
    os.makedirs(KB_DIR, exist_ok=True)
    files = glob.glob(os.path.join(KB_DIR, "**", "*"), recursive=True)
    files = [f for f in files if os.path.isfile(f) and f.lower().endswith((".txt", ".md", ".pdf"))]

    chunks, sources = [], []
    for path in files:
        try:
            text = _read_file(path)
        except Exception as e:
            print(f"Skipping {path}: {e}")
            continue
        for chunk in _chunk_text(text):
            chunks.append(chunk)
            sources.append(os.path.basename(path))

    if not chunks:
        print("No documents found in knowledge_base/. Add .txt/.md/.pdf files and rebuild.")
        return

    model = _get_model()
    embeddings = model.encode(chunks, show_progress_bar=False, normalize_embeddings=True)

    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"chunks": chunks, "sources": sources, "embeddings": embeddings}, f)

    print(f"Indexed {len(chunks)} chunks from {len(files)} files.")


def _load_index():
    if not os.path.exists(INDEX_PATH):
        return None
    with open(INDEX_PATH, "rb") as f:
        return pickle.load(f)


def retrieve(query, top_k=3):
    """Return top_k most relevant chunks for a query."""
    index = _load_index()
    if index is None:
        return []

    model = _get_model()
    query_emb = model.encode([query], normalize_embeddings=True)[0]

    embeddings = index["embeddings"]
    scores = embeddings @ query_emb  # cosine similarity (vectors are normalized)
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for i in top_indices:
        if scores[i] > 0.25:  # relevance threshold, tune as needed
            results.append({"text": index["chunks"][i], "source": index["sources"][i], "score": float(scores[i])})
    return results


def answer_with_context(query, ask_ai_fn):
    """
    Retrieve relevant chunks and build an augmented prompt,
    then call the existing ask_ai function from will.py.
    """
    matches = retrieve(query, top_k=3)
    if not matches:
        return ask_ai_fn(query)  # no relevant docs, fall back to normal chat

    context = "\n\n".join(f"[From {m['source']}]\n{m['text']}" for m in matches)
    augmented_prompt = (
        f"Use the following personal notes if relevant to answer the question.\n\n"
        f"{context}\n\n"
        f"Question: {query}\n"
        f"Answer using the notes above when they're relevant. If they aren't relevant, answer normally."
    )
    return ask_ai_fn(augmented_prompt)