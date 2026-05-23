from sentence_transformers import SentenceTransformer
import numpy as np

# Load once at module level
# Downloads on first run (~420MB), cached after that
print("Loading embedding model: all-mpnet-base-v2...")
model = SentenceTransformer("all-mpnet-base-v2")
print("Embedding model loaded")


def embed_text(text: str) -> list:
    """
    Embed a single string.
    Returns a list of 768 floats.
    """
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_batch(texts: list[str]) -> list[list]:
    """
    Embed multiple strings at once.
    Faster than embedding one by one.
    Returns list of embeddings.
    """
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return embeddings.tolist()


def cosine_similarity(vec1: list, vec2: list) -> float:
    """
    Compute similarity between two embeddings.
    Since we normalize, dot product = cosine similarity.
    """
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b))