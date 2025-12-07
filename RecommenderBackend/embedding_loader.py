import pandas as pd
import numpy as np

def load_movie_embeddings(path: str):
    df = pd.read_parquet(path)

    # movie_embeddings = np.vstack(df["embedding"].values).astype("float32")
    movie_embeddings = np.vstack(df["embedding"].values).astype("float32")
    movie_embeddings /= np.linalg.norm(movie_embeddings, axis=1, keepdims=True)


    movie_metadata = df[[
        "movie_id",
        "title",
        "year",
        "genres",
        "tmdb_overview",
        "tmdb_top_cast"
    ]].to_dict(orient="records")

    return movie_embeddings, movie_metadata


def load_user_embeddings(path: str):
    df = pd.read_parquet(path)

    user_vectors = {}
    for _, row in df.iterrows():
        user_vectors[row["user_id"]] = np.array(row["embedding"], dtype="float32")

    return user_vectors
