import faiss
import numpy as np

class MovieIndex:
    def __init__(self, embeddings: np.ndarray):
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

    def search(self, query_vec: np.ndarray, k=10):
        scores, idxs = self.index.search(
            query_vec.reshape(1, -1).astype("float32"), k
        )
        return idxs[0], scores[0]
