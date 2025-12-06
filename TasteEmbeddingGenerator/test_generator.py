# TasteEmbeddingGenerator/test_generator.py

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .Generator import TasteEmbeddingConfig, TasteEmbeddingGenerator


def assert_no_nan(vecs, name: str):
    arr = np.array(list(vecs), dtype=float)
    if np.isnan(arr).any():
        raise AssertionError(f"[ERROR] NaN detected in {name}")
    print(f"[OK] No NaN in {name}")


def main():
    project_root = Path(__file__).resolve().parents[1]

    cfg = TasteEmbeddingConfig(
        project_root=project_root,
        backend_type="sentence-transformers",
        model_name="BAAI/bge-base-en-v1.5",
        movie_sources=["movielens", "movietweetings", "inspired"],  # smoke test - Only movielens
        batch_size=32,
        rating_threshold=4.0,
        min_movies=3,
    )

    gen = TasteEmbeddingGenerator(cfg)

    print(">>> Running small movie embedding pipeline (limit=100)")
    movie_emb_path = gen.build_movie_embeddings(movie_limit := 100)

    print(">>> Running user embedding pipeline")
    user_emb_path = gen.build_user_embeddings(movie_emb_path)

    # ---- sanity check: movie embeddings ----
    mdf = pd.read_parquet(movie_emb_path)
    print("[INFO] movie_embeddings head:")
    print(mdf.head(2))

    assert "embedding" in mdf.columns
    first_vec = mdf["embedding"].iloc[0]
    print(f"[INFO] Movie embedding dim = {len(first_vec)}")
    assert_no_nan(mdf["embedding"], "movie_embeddings")

    # ---- sanity check: user embeddings ----
    udf = pd.read_parquet(user_emb_path)
    print("[INFO] user_embeddings head:")
    print(udf.head(2))

    assert "embedding" in udf.columns
    u_first = udf["embedding"].iloc[0]
    print(f"[INFO] User embedding dim = {len(u_first)}")
    assert_no_nan(udf["embedding"], "user_embeddings")

    print("\n>>> All sanity checks passed for small test run!")


if __name__ == "__main__":
    main()
