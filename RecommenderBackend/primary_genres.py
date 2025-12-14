from embedding_loader import load_movie_embeddings
from config import MOVIE_EMBED_PATH
from visualizations.clusters import compute_per_movie_cluster_genre

emb, meta = load_movie_embeddings(MOVIE_EMBED_PATH)
labels, cluster_genres, movie_cluster_genre = compute_per_movie_cluster_genre(emb, meta)

# Example: dump to CSV you can import into the DB
import pandas as pd
df = pd.DataFrame({
    "movie_id": [m["movie_id"] for m in meta],
    "cluster_id": labels,
    "cluster_genre": movie_cluster_genre,
})
df.to_csv("movie_cluster_genres.csv", index=False)
