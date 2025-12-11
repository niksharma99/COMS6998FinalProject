# TasteEmbeddingGenerator/analysis.py

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple, Optional

import argparse
import logging
import random

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# Paths helpers
# ---------------------------------------------------------------------------

def get_project_root() -> Path:
    """Assume this file lives in TasteEmbeddingGenerator/."""
    return Path(__file__).resolve().parents[1]


def get_default_paths() -> Dict[str, Path]:
    project_root = get_project_root()
    artifacts = project_root / "TasteEmbeddingGenerator" / "artifacts"
    processed = project_root / "Dataset" / "processed"

    return {
        "movie_embeddings": artifacts / "movie_embeddings.parquet",
        "user_embeddings": artifacts / "user_embeddings.parquet",
        "movielens_ratings": processed / "movielens_ratings.csv",
    }

def get_genre_field(row: pd.Series) -> Optional[str]:
    """Safely pick a genre-like string from row (tmdb_genres → genres → genre)."""
    for col in ("tmdb_genres", "genres", "genre"):
        if col in row.index:
            val = row[col]
            if not pd.isna(val):
                return str(val)
    return None


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_movie_embeddings(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Movie embeddings not found: {path}")
    df = pd.read_parquet(path)
    logger.info(f"[analysis] Loaded movie embeddings: {df.shape} from {path}")
    return df


def load_user_embeddings(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"User embeddings not found: {path}")
    df = pd.read_parquet(path)
    logger.info(f"[analysis] Loaded user embeddings: {df.shape} from {path}")
    return df


def load_movielens_ratings(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Ratings file not found: {path}")
    df = pd.read_csv(path)
    logger.info(f"[analysis] Loaded MovieLens ratings: {df.shape} from {path}")
    return df


# ---------------------------------------------------------------------------
# 0. Basic health checks
# ---------------------------------------------------------------------------

def movie_embedding_healthcheck(movie_df: pd.DataFrame) -> None:
    """Check norms and basic stats of movie embeddings."""
    if "embedding" not in movie_df.columns:
        raise ValueError("movie_df must contain 'embedding' column")

    emb = np.stack(movie_df["embedding"].tolist(), axis=0)  # (N, D)
    norms = np.linalg.norm(emb, axis=1)

    logger.info(
        "[analysis] Movie embedding norms: min=%.4f mean=%.4f max=%.4f",
        float(norms.min()),
        float(norms.mean()),
        float(norms.max()),
    )
    logger.info(
        "[analysis] Movie embedding per-dim std (first 10 dims): %s",
        np.round(emb.std(axis=0)[:10], 4),
    )


# ---------------------------------------------------------------------------
# 1. Nearest neighbors sanity check
# ---------------------------------------------------------------------------

def find_movie_by_keyword(df: pd.DataFrame, keyword: str, k: int = 5) -> pd.DataFrame:
    cond = pd.Series(False, index=df.index)

    for col in ["title", "tmdb_title"]:
        if col in df.columns:
            cond = cond | df[col].astype(str).str.contains(keyword, case=False, na=False)

    result = df[cond]
    return result.head(k)


def nearest_neighbors(
    movie_df: pd.DataFrame,
    anchor_title_keyword: str,
    top_k: int = 10,
) -> Tuple[pd.Series, pd.DataFrame]:
    """Return anchor movie row and its top-k most similar movies."""
    if "embedding" not in movie_df.columns:
        raise ValueError("movie_df must contain 'embedding' column")

    anchor_candidates = find_movie_by_keyword(movie_df, anchor_title_keyword, k=1)
    if anchor_candidates.empty:
        raise ValueError(f"No movie found with keyword '{anchor_title_keyword}'")

    anchor = anchor_candidates.iloc[0]
    emb = np.stack(movie_df["embedding"].tolist(), axis=0)
    anchor_vec = np.array(anchor["embedding"], dtype=np.float32).reshape(1, -1)

    sims = cosine_similarity(anchor_vec, emb)[0]
    movie_df = movie_df.copy()
    movie_df["similarity"] = sims

    topk = movie_df.sort_values("similarity", ascending=False).head(top_k + 1)

    topk_wo_anchor = topk[topk["movie_id"] != anchor["movie_id"]].head(top_k)

    return anchor, topk_wo_anchor


def run_nearest_neighbors_demo(movie_df: pd.DataFrame, anchor_keyword: str) -> None:
    anchor, topk = nearest_neighbors(movie_df, anchor_keyword, top_k=10)

    logger.info("=== Nearest Neighbors Demo ===")
    logger.info("Anchor: %s | genres=%s | source=%s",
                anchor.get("title") or anchor.get("tmdb_title"),
                anchor.get("tmdb_genres") or anchor.get("genres"),
                anchor.get("source"))
    logger.info("Top-10 similar movies:")
    cols = ["title", "tmdb_title", "tmdb_genres", "genres", "source", "similarity"]
    logger.info("\n%s", topk[cols].to_string(index=False))


# ---------------------------------------------------------------------------
# 2. Genre-based similarity: same-genre vs diff-genre
# ---------------------------------------------------------------------------

def has_genre(genres: Optional[str], g: str) -> bool:
    if not isinstance(genres, str):
        return False
    return g.lower() in genres.lower()


def sample_genre_pairs(
    movie_df: pd.DataFrame,
    genre: str = "Drama",
    n_pairs: int = 2000,
) -> Tuple[np.ndarray, np.ndarray]:
    """Sample random movie pairs and compute similarity between same-genre vs diff-genre."""
    emb = np.stack(movie_df["embedding"].tolist(), axis=0)
    idx = np.arange(len(movie_df))

    same_sims: List[float] = []
    diff_sims: List[float] = []

    for _ in range(n_pairs):
        i, j = np.random.choice(idx, size=2, replace=False)
        row_i = movie_df.iloc[i]
        row_j = movie_df.iloc[j]

        gi = get_genre_field(row_i)
        gj = get_genre_field(row_j)

        si = has_genre(gi, genre)
        sj = has_genre(gj, genre)

        sim = float(np.dot(emb[i], emb[j]))  # embeddings are normalized

        if si and sj:
            same_sims.append(sim)
        elif si != sj:
            diff_sims.append(sim)

    return np.array(same_sims), np.array(diff_sims)


def run_genre_similarity_check(movie_df: pd.DataFrame, genre: str = "Drama") -> None:
    same, diff = sample_genre_pairs(movie_df, genre=genre, n_pairs=2000)
    logger.info("=== Genre similarity check [%s] ===", genre)
    logger.info(
        "same-genre mean=%.4f (n=%d) | diff-genre mean=%.4f (n=%d)",
        float(same.mean()) if len(same) else float("nan"),
        len(same),
        float(diff.mean()) if len(diff) else float("nan"),
        len(diff),
    )


# ---------------------------------------------------------------------------
# 3. Simple offline recommendation metric (HitRate@K)
#    NOTE: This uses the *existing* user embeddings, which were built on all ratings.
#          Strict train/test split is possible later if needed.
# ---------------------------------------------------------------------------

def build_user_vecs(user_df: pd.DataFrame) -> Dict[int, np.ndarray]:
    """Map MovieLens numeric user_id -> embedding vector.
    """
    user_vecs: Dict[int, np.ndarray] = {}

    for _, row in user_df.iterrows():
        uid = row["user_id"]
        vec = np.array(row["embedding"], dtype=np.float32)

        numeric_id = None

        # case 1: already number
        if isinstance(uid, (int, np.integer)):
            numeric_id = int(uid)

        # case 2: str
        elif isinstance(uid, str):
            import re

            m = re.search(r"(\d+)", uid)
            if m:
                numeric_id = int(m.group(1))

        if numeric_id is not None:
            user_vecs[numeric_id] = vec

    logger.info("[analysis] Built %d numeric MovieLens user vectors", len(user_vecs))
    return user_vecs




def build_movie_vecs_for_movielens(movie_df: pd.DataFrame) -> Dict[int, np.ndarray]:
    """Map MovieLens movie_id -> embedding vector."""
    movie_vecs: Dict[int, np.ndarray] = {}
    df_ml = movie_df[movie_df["source"] == "movielens"]

    for _, row in df_ml.iterrows():
        mid = int(row["movie_id"])
        vec = np.array(row["embedding"], dtype=np.float32)
        movie_vecs[mid] = vec

    logger.info("[analysis] Built %d MovieLens movie vectors", len(movie_vecs))
    return movie_vecs


def recommend_for_user(
    user_id: int,
    user_vecs: Dict[int, np.ndarray],
    movie_vecs: Dict[int, np.ndarray],
    top_k: int = 50,
) -> List[int]:
    """Return top-k movie_ids for given user based on dot-product similarity."""
    uvec = user_vecs.get(user_id)
    if uvec is None:
        return []

    sims: List[Tuple[int, float]] = []
    for mid, mvec in movie_vecs.items():
        sims.append((mid, float(np.dot(uvec, mvec))))

    sims.sort(key=lambda x: x[1], reverse=True)
    return [mid for mid, _ in sims[:top_k]]


def run_hitrate_eval(
    ratings: pd.DataFrame,
    user_df: pd.DataFrame,
    movie_df: pd.DataFrame,
    rating_threshold: float = 4.0,
    top_k: int = 10,
    max_users: int = 500,
) -> None:
    """
    Simple HitRate@K evaluation:
      - For each user, pick one high-rated movie as the 'target'
      - Check if it appears in the top-K list from the user embedding
    NOTE: user embeddings are built from all ratings (not a strict train/test split).
    """
    user_vecs = build_user_vecs(user_df)
    movie_vecs = build_movie_vecs_for_movielens(movie_df)

    # Filter to positive interactions
    pos = ratings[ratings["rating"] >= rating_threshold].copy()
    logger.info(
        "[analysis] Found %d positive (rating>=%.1f) interactions for eval",
        len(pos),
        rating_threshold,
    )

    # For each user: randomly pick one positive movie as 'target'
    pos = pos.sort_values("timestamp") if "timestamp" in pos.columns else pos
    grouped = pos.groupby("userId")

    users = list(grouped.groups.keys())
    random.shuffle(users)
    users = users[:max_users]

    hits = 0
    total = 0

    for uid in users:
        if uid not in user_vecs:
            continue
        group = grouped.get_group(uid)
        # Pick last or random positive movie
        target_row = group.iloc[-1]
        target_mid = int(target_row["movieId"])

        recs = recommend_for_user(uid, user_vecs, movie_vecs, top_k=top_k)
        if not recs:
            continue

        total += 1
        if target_mid in recs:
            hits += 1

    hitrate = hits / total if total > 0 else 0.0
    logger.info(
        "[analysis] HitRate@%d over %d users = %.4f",
        top_k,
        total,
        hitrate,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analysis & sanity checks for TasteEmbeddingGenerator embeddings."
    )
    parser.add_argument(
        "--anchor",
        type=str,
        default="Toy Story",
        help="Keyword to pick an anchor movie for nearest-neighbor demo.",
    )
    parser.add_argument(
        "--genre",
        type=str,
        default="Drama",
        help="Genre name for genre-similarity analysis.",
    )
    parser.add_argument(
        "--run-hitrate",
        action="store_true",
        help="Run simple HitRate@K evaluation on MovieLens ratings.",
    )
    parser.add_argument(
        "--topk",
        type=int,
        default=10,
        help="Top-K for nearest neighbors and HitRate@K.",
    )
    parser.add_argument(
        "--max-users",
        type=int,
        default=500,
        help="Max number of users to sample for HitRate eval.",
    )

    args = parser.parse_args()
    paths = get_default_paths()

    # Load embeddings
    movie_df = load_movie_embeddings(paths["movie_embeddings"])
    user_df = load_user_embeddings(paths["user_embeddings"])

    # 0) basic health check
    movie_embedding_healthcheck(movie_df)

    # 1) nearest neighbors demo
    try:
        run_nearest_neighbors_demo(movie_df, args.anchor)
    except Exception as e:
        logger.warning(f"[analysis] Nearest neighbors demo failed: {e}")

    # 2) genre similarity
    try:
        run_genre_similarity_check(movie_df, genre=args.genre)
    except Exception as e:
        logger.warning(f"[analysis] Genre similarity check failed: {e}")

    # 3) HitRate@K eval
    if args.run_hitrate:
        ratings = load_movielens_ratings(paths["movielens_ratings"])
        run_hitrate_eval(
            ratings=ratings,
            user_df=user_df,
            movie_df=movie_df,
            rating_threshold=4.0,
            top_k=args.topk,
            max_users=args.max_users,
        )


if __name__ == "__main__":
    main()
