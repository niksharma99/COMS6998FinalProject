"""
comparison.py

Compare two embedding sets:
- artifacts/             (e.g., OpenAI embeddings)
- artifacts_huggingface/ (e.g., HuggingFace/BGE embeddings)

Metrics:
  1) Genre separation (same-genre vs diff-genre cosine similarity)
  2) HitRate@K on MovieLens ratings

Usage:
    python comparison.py
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, List, Any

import numpy as np
import pandas as pd
from tqdm import tqdm

# ---------------- Config & Paths ----------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ARTIFACTS_OPENAI = PROJECT_ROOT / "TasteEmbeddingGenerator" / "artifacts"
ARTIFACTS_HF = PROJECT_ROOT / "TasteEmbeddingGenerator" / "artifacts_huggingface"

DATA_PROCESSED = PROJECT_ROOT / "Dataset" / "processed"
MOVIELENS_MOVIES = DATA_PROCESSED / "movielens_movies_tmdb.csv"
MOVIELENS_RATINGS = DATA_PROCESSED / "movielens_ratings.csv"

K_HITRATE = 10
RATING_THRESHOLD = 4.0
MIN_MOVIES_PER_USER = 3
MAX_USERS_FOR_EVAL = 500  # evaluate on at most this many users
RANDOM_SEED = 42


# ---------------- Small helpers ----------------

def _load_embedding_parquet(path: Path) -> Tuple[pd.DataFrame, np.ndarray]:
    df = pd.read_parquet(path)
    if "embedding" not in df.columns:
        raise ValueError(f"'embedding' column not found in {path}")

    vecs = np.stack(df["embedding"].to_numpy()).astype("float32")
    # L2 normalize for cosine
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
    vecs = vecs / norms
    return df, vecs


def _parse_movielens_user_id(raw: Any) -> int | None:
    if not isinstance(raw, str):
        return None

    s = raw.strip()
    if s.startswith("movielens:"):
        tail = s.split(":", 1)[1]
        return int(tail) if tail.isdigit() else None

    if s.isdigit():
        return int(s)

    return None


# ---------------- EmbeddingSet ----------------

@dataclass
class EmbeddingSet:
    name: str
    artifacts_dir: Path

    movie_df: pd.DataFrame | None = None
    movie_vecs: np.ndarray | None = None
    user_df: pd.DataFrame | None = None
    user_vecs: np.ndarray | None = None

    ml_movie_df: pd.DataFrame | None = None
    ml_movie_vecs: np.ndarray | None = None
    ml_movie_id_to_idx: Dict[int, int] | None = None

    def load(self):
        movie_path = self.artifacts_dir / "movie_embeddings.parquet"
        user_path = self.artifacts_dir / "user_embeddings.parquet"

        print(f"[{self.name}] Loading movie embeddings from {movie_path}")
        self.movie_df, self.movie_vecs = _load_embedding_parquet(movie_path)
        print(f"[{self.name}] movie_vecs shape = {self.movie_vecs.shape}")

        print(f"[{self.name}] Loading user embeddings from {user_path}")
        self.user_df, self.user_vecs = _load_embedding_parquet(user_path)
        print(f"[{self.name}] user_vecs shape = {self.user_vecs.shape}")

        self._build_movielens_movie_view()

    # ---------- MovieLens movie subset ----------

    def _build_movielens_movie_view(self):
        """
        - ml_movie_df: movieId, title, genres, embedding 등
        - ml_movie_vecs: (N_movies, D)
        - ml_movie_id_to_idx: movieId -> row index in ml_movie_vecs
        """
        ml = pd.read_csv(MOVIELENS_MOVIES, low_memory=False)

        if "title" in ml.columns:
            ml = ml.rename(columns={"title": "title_ml"})
        if "genres" in ml.columns:
            ml = ml.rename(columns={"genres": "genres_ml"})

        # tmdb_id string
        if "tmdb_id" not in ml.columns or "tmdb_id" not in self.movie_df.columns:
            raise ValueError("tmdb_id column required in MovieLens and movie embeddings")

        ml["tmdb_id"] = ml["tmdb_id"].astype(str)
        self.movie_df["tmdb_id"] = self.movie_df["tmdb_id"].astype(str)

        # MovieLens  + embedding join (criteria: tmdb_id)
        merged = ml[["movieId", "title_ml", "genres_ml", "tmdb_id"]].merge(
            self.movie_df[["tmdb_id", "embedding"]],
            on="tmdb_id",
            how="inner",
        )

        def agg_embedding(rows: pd.Series) -> np.ndarray:
            arrs = np.stack(rows.to_numpy())
            return arrs.mean(axis=0)

        grouped = merged.groupby("movieId").agg(
            title_ml=("title_ml", "first"),
            genres_ml=("genres_ml", "first"),
            embedding=("embedding", agg_embedding),
        )

        movie_ids = grouped.index.to_numpy()
        vecs = np.stack(grouped["embedding"].to_numpy()).astype("float32")
        norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
        vecs = vecs / norms

        self.ml_movie_df = grouped.reset_index()
        self.ml_movie_vecs = vecs
        self.ml_movie_id_to_idx = {int(mid): i for i, mid in enumerate(movie_ids)}

        print(
            f"[{self.name}] MovieLens movies with embeddings: "
            f"{self.ml_movie_vecs.shape[0]} (of {ml.shape[0]})"
        )
        print(
            f"[{self.name}] Example ML movies:\n",
            self.ml_movie_df.head(3)[["movieId", "title_ml", "genres_ml"]],
        )

    # ---------- Genre separation ----------

    def genre_separation(self, genre: str = "Drama",
                         max_pairs: int = 5000) -> Tuple[float, float]:
        """
        calculate mean of cosine similarity of difference between same-genre / diff-genre pair

        Returns:
            (same_mean, diff_mean)
        """
        df = self.ml_movie_df.copy()

        genre_col = "genres_ml"
        if genre_col not in df.columns:
            raise ValueError(f"{genre_col} column not found in ml_movie_df")

        def has_genre(s: str) -> bool:
            if not isinstance(s, str):
                return False
            # MovieLens format: "Adventure|Children's|Fantasy"
            parts = [p.strip().lower() for p in s.split("|")]
            return genre.lower() in parts

        df["has_genre"] = df[genre_col].apply(has_genre)

        same_idx = df[df["has_genre"]].index.to_numpy()
        diff_idx = df[~df["has_genre"]].index.to_numpy()

        if len(same_idx) == 0 or len(diff_idx) == 0:
            raise ValueError(f"No movies found with/without genre '{genre}'")

        rng = np.random.default_rng(RANDOM_SEED)
        same_idx = rng.choice(same_idx, size=min(len(same_idx), 200), replace=False)
        diff_idx = rng.choice(diff_idx, size=min(len(diff_idx), 200), replace=False)

        same_vecs = self.ml_movie_vecs[same_idx]
        diff_vecs = self.ml_movie_vecs[diff_idx]

        sims_same: List[float] = []
        sims_diff: List[float] = []

        # same-genre pairs
        for i in range(len(same_vecs)):
            for j in range(i + 1, len(same_vecs)):
                sims_same.append(float(np.dot(same_vecs[i], same_vecs[j])))
                if len(sims_same) >= max_pairs:
                    break
            if len(sims_same) >= max_pairs:
                break

        # diff-genre pairs
        for i in range(len(same_vecs)):
            for j in range(len(diff_vecs)):
                sims_diff.append(float(np.dot(same_vecs[i], diff_vecs[j])))
                if len(sims_diff) >= max_pairs:
                    break
            if len(sims_diff) >= max_pairs:
                break

        same_mean = float(np.mean(sims_same))
        diff_mean = float(np.mean(sims_diff))
        gap = same_mean - diff_mean

        print(
            f"[{self.name}] Genre separation ({genre}): "
            f"same_mean={same_mean:.4f}, diff_mean={diff_mean:.4f}, gap={gap:.4f}"
        )
        return same_mean, diff_mean

    # ---------- HitRate@K ----------

    def hitrate_at_k(self, k: int = K_HITRATE) -> float:
        """
        Evaluate HitRate@K using MovieLens ratings

        - ratings: userId, movieId, rating
        - user_embeddings: use if user_id is 'movielens:123' or '123'
        """
        ratings = pd.read_csv(MOVIELENS_RATINGS)
        ratings = ratings[ratings["rating"] >= RATING_THRESHOLD].copy()

        user_groups = ratings.groupby("userId")
        users: List[Tuple[int, np.ndarray]] = []
        for uid, grp in user_groups:
            if len(grp) >= MIN_MOVIES_PER_USER:
                users.append((int(uid), grp["movieId"].to_numpy()))

        print(f"[{self.name}] Users with >= {MIN_MOVIES_PER_USER} positives: {len(users)}")

        # user_id → embedding index
        if "user_id" not in self.user_df.columns:
            raise ValueError("user_embeddings.parquet must contain 'user_id' column.")

        user_id_to_idx: Dict[int, int] = {}
        for i, raw_uid in enumerate(self.user_df["user_id"].to_numpy()):
            ml_uid = _parse_movielens_user_id(raw_uid)
            if ml_uid is not None:
                user_id_to_idx[ml_uid] = i

        print(f"[{self.name}] MovieLens user embeddings available: {len(user_id_to_idx)}")

        rng = np.random.default_rng(RANDOM_SEED)

        rng.shuffle(users)
        users_eval = users[: min(len(users), MAX_USERS_FOR_EVAL)]
        print(f"[{self.name}] Evaluating HR@{k} on {len(users_eval)} users")

        hits = 0
        total = 0

        movie_vecs = self.ml_movie_vecs
        for uid, pos_movies in tqdm(users_eval, desc=f"{self.name} HR@{k}"):
            uidx = user_id_to_idx.get(uid, None)
            if uidx is None:
                continue

            target = int(rng.choice(pos_movies))
            target_idx = self.ml_movie_id_to_idx.get(target, None)
            if target_idx is None:
                continue

            user_vec = self.user_vecs[uidx]  # (D,)

            scores = movie_vecs @ user_vec  # (N_movies,)
            topk_idx = np.argpartition(-scores, k)[:k]

            if target_idx in topk_idx:
                hits += 1
            total += 1

        hr = hits / total if total > 0 else float("nan")
        print(f"[{self.name}] HitRate@{k} = {hr:.4f} (hits={hits}, total={total})")
        return hr


# ---------------- Main ----------------

def main():
    openai_set = EmbeddingSet(name="OpenAI", artifacts_dir=ARTIFACTS_OPENAI)
    hf_set = EmbeddingSet(name="HuggingFace", artifacts_dir=ARTIFACTS_HF)

    print("=== Loading embeddings ===")
    openai_set.load()
    hf_set.load()

    print("\n=== Genre separation (Drama) ===")
    oa_same, oa_diff = openai_set.genre_separation(genre="Drama")
    hf_same, hf_diff = hf_set.genre_separation(genre="Drama")

    print("\n=== HitRate@K comparison ===")
    oa_hr = openai_set.hitrate_at_k(k=K_HITRATE)
    hf_hr = hf_set.hitrate_at_k(k=K_HITRATE)

    print("\n=== Summary ===")
    print(
        f"OpenAI:      HR@{K_HITRATE} = {oa_hr:.4f}, "
        f"Drama gap = {oa_same - oa_diff:.4f}"
    )
    print(
        f"HuggingFace: HR@{K_HITRATE} = {hf_hr:.4f}, "
        f"Drama gap = {hf_same - hf_diff:.4f}"
    )


if __name__ == "__main__":
    main()
