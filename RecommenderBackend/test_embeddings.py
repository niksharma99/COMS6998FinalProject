from embedding_loader import load_movie_embeddings, load_user_embeddings
from config import MOVIE_EMBED_PATH, USER_EMBED_PATH
import numpy as np

movie_vecs, movie_meta = load_movie_embeddings(MOVIE_EMBED_PATH)
user_vecs = load_user_embeddings(USER_EMBED_PATH)

print("Movie Embeddings:", movie_vecs.shape)
print("Num Movies:", len(movie_meta))
print("Num Users:", len(user_vecs))

# Pick random user
random_user = next(iter(user_vecs.values()))

assert movie_vecs.shape[1] == random_user.shape[0], "DIMENSION MISMATCH"
assert not np.isnan(movie_vecs).any(), "NaNs in movie embeddings"
assert not np.isnan(random_user).any(), "NaNs in user embeddings"

print("✅ Embedding sanity check passed!")
