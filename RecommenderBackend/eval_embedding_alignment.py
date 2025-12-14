#!/usr/bin/env python3
# RecommenderBackend/eval_embedding_alignment.py

"""
Quantitative evaluation: embedding alignment.

We measure how well the recommended movies align with the user's fused
taste vector in embedding space, using cosine similarity.

Input:
  - rec_log.jsonl (written by recommender.recommend)
  - movie_embeddings.parquet (via load_movie_embeddings)

Output:
  - Prints mean & std cosine similarity for the recommended items.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from config import MOVIE_EMBED_PATH, FINAL_K
from embedding_loader import load_movie_embeddings

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "rec_log.jsonl"


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b)


def main():
    # Load movie embeddings (for recommended items)
    movie_embeddings, movie_metadata = load_movie_embeddings(MOVIE_EMBED_PATH)
    movie_embeddings = np.asarray(movie_embeddings, dtype=np.float32)

    if not LOG_PATH.exists():
        print(f"No log file found at {LOG_PATH}. Did you run the recommender yet?")
        return

    sims = []

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            user_vec_list = rec.get("user_vec")
            cand_indices = rec.get("candidate_indices")
            final_k = int(rec.get("final_k", FINAL_K))

            if user_vec_list is None or cand_indices is None:
                continue

            user_vec = np.asarray(user_vec_list, dtype=np.float32)
            # ensure normalized
            u_norm = np.linalg.norm(user_vec)
            if u_norm > 0:
                user_vec = user_vec / u_norm

            cand_indices = [int(i) for i in cand_indices][:final_k]

            for idx in cand_indices:
                if idx < 0 or idx >= len(movie_embeddings):
                    continue
                mv = movie_embeddings[idx]
                mv_norm = np.linalg.norm(mv)
                if mv_norm > 0:
                    mv = mv / mv_norm
                sims.append(cosine_sim(user_vec, mv))

    if not sims:
        print("No similarities computed. rec_log.jsonl may be empty.")
        return

    sims_arr = np.asarray(sims, dtype=np.float32)
    mean_sim = float(np.mean(sims_arr))
    std_sim = float(np.std(sims_arr))

    df = pd.DataFrame(
        [
            {
                "setting": "current recommender (embedding-based + GPT explanation)",
                "mean_cosine_similarity": mean_sim,
                "std_cosine_similarity": std_sim,
                "num_pairs": len(sims_arr),
            }
        ]
    )
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
