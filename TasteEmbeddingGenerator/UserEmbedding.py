# TasteEmbeddingGenerator/UserEmbedding.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import logging
import numpy as np
import pandas as pd

from .embeddings_backend import BaseEmbeddingBackend  # sentence-transformers / OpenAI 공통 인터페이스

logger = logging.getLogger(__name__)


@dataclass
class UserEmbeddingConfig:
    """
    User embedding Setting.

    - processed_dir: Dataset/processed
    - movie_embedding_path: movie_embeddings.parquet path
    - embedder: baend for user text embedding
                (SentenceTransformerBackend, OpenAIEmbeddingBackend.. BaseEmbeddingBackend ..)
    - rating_threshold: rating based minimum score to consider "favorite movie"
    - min_movies: only making user embedding >= min_movies
    - source_filter: source for movie embedding (ex: "movielens", None - total)
    - use_text: whether ccpe / inspired / redial text use or not
    - mix_alpha: rating vs text ratio for final user embedding,
                 final = alpha * rating_vec + (1 - alpha) * text_vec
    """

    processed_dir: Path
    movie_embedding_path: Path
    embedder: BaseEmbeddingBackend

    rating_threshold: float = 4.0
    min_movies: int = 3
    source_filter: Optional[str] = "movielens" # ["movielens", "movietweetings", "inspired", None]

    use_text: bool = True
    mix_alpha: float = 0.7  # α: rating ratio, (1-α): text ratio


class UserEmbeddingGenerator:
    """Build user embeddings from ratings + (optional) user text profiles + precomputed movie embeddings."""

    def __init__(self, config: UserEmbeddingConfig):
        self.config = config
        self.processed_dir = config.processed_dir
        self.movie_embedding_path = config.movie_embedding_path
        self.embedder = config.embedder

        self._movie_emb_df: Optional[pd.DataFrame] = None
        self._movie_vecs: Dict[int, np.ndarray] = {}

    # ---------- helper: movie embedding loading ----------

    def _load_movie_embeddings(self):
        if self._movie_emb_df is not None:
            return

        if not self.movie_embedding_path.exists():
            raise FileNotFoundError(
                f"Movie embedding file not found: {self.movie_embedding_path}"
            )
        df = pd.read_parquet(self.movie_embedding_path)

        if self.config.source_filter is not None and "source" in df.columns:
            df = df[df["source"] == self.config.source_filter].copy()
            logger.info(
                f"[UserEmbedding] Filtered movies by source={self.config.source_filter}: {df.shape}"
            )

        self._movie_emb_df = df

        # movie_id -> vector mapping
        self._movie_vecs = {}
        for _, row in df.iterrows():
            mid = int(row["movie_id"])
            vec = np.array(row["embedding"], dtype=np.float32)
            self._movie_vecs[mid] = vec

        logger.info(
            f"[UserEmbedding] Loaded {len(self._movie_vecs)} movie embeddings "
            f"from {self.movie_embedding_path}"
        )

    def _load_ratings(self) -> pd.DataFrame:
        path = self.processed_dir / "movielens_ratings.csv"
        if not path.exists():
            raise FileNotFoundError(f"Ratings file not found: {path}")
        df = pd.read_csv(path)
        return df

    # ---------- Step 1: rating based user embedding ----------

    def _build_rating_user_embeddings(self) -> pd.DataFrame:
        """
        create MovieLens rating based user embedding.

        return:
          user_id (str), embedding_rating (list[float]), num_movies (int)
        """
        self._load_movie_embeddings()
        ratings = self._load_ratings()

        liked = ratings[ratings["rating"] >= self.config.rating_threshold].copy()
        logger.info(
            f"[UserEmbedding] Using {len(liked)} ratings with rating >= {self.config.rating_threshold}"
        )

        user_groups = liked.groupby("userId")
        user_ids: List[str] = []
        user_vecs: List[List[float]] = []
        movie_counts: List[int] = []

        for uid, group in user_groups:
            movie_ids = group["movieId"].tolist()
            vecs = [
                self._movie_vecs[mid]
                for mid in movie_ids
                if mid in self._movie_vecs
            ]

            if len(vecs) < self.config.min_movies:
                continue

            mat = np.stack(vecs, axis=0)  # (num_movies, dim)
            mean_vec = mat.mean(axis=0)

            user_ids.append(str(uid)) 
            user_vecs.append(mean_vec.tolist())
            movie_counts.append(len(vecs))

        df_users = pd.DataFrame(
            {
                "user_id": user_ids,
                "embedding_rating": user_vecs,
                "num_movies": movie_counts,
            }
        )

        logger.info(
            f"[UserEmbedding] Built rating-based user embeddings for {len(df_users)} users"
        )
        return df_users

    # ---------- Step 2: text based user profile loading ----------

    def _build_ccpe_text_profiles(self) -> pd.DataFrame:
        """
        ccpe_dialogue.csv:
          dialog_id,utterance_index,speaker,text
        """
        path = self.processed_dir / "ccpe_dialogues.csv"
        if not path.exists():
            logger.info("[UserEmbedding] ccpe_dialogue.csv not found, skipping CCPE.")
            return pd.DataFrame(columns=["user_id", "text_profile"])

        df = pd.read_csv(path)
        required = {"dialog_id", "text"}
        if not required.issubset(df.columns):
            logger.warning(
                "[UserEmbedding] ccpe_dialogue.csv missing required columns "
                f"{required - set(df.columns)}. Skipping CCPE."
            )
            return pd.DataFrame(columns=["user_id", "text_profile"])

        grouped = df.groupby("dialog_id")["text"].apply(
            lambda xs: " ".join(str(t) for t in xs if isinstance(t, str))
        )
        profiles = grouped.reset_index()
        profiles["user_id"] = "ccpe:" + profiles["dialog_id"].astype(str)
        profiles.rename(columns={"text": "text_profile"}, inplace=True)
        # text_profile rename
        profiles = profiles.rename(columns={0: "text_profile"}) if 0 in profiles.columns else profiles

        if "text_profile" not in profiles.columns:
            profiles["text_profile"] = grouped.values

        return profiles[["user_id", "text_profile"]]

    def _build_inspired_text_profiles(self) -> pd.DataFrame:
        """
        inspired_dialogs.csv:
          dialog_id,utt_id,speaker,turn_id,text,...
        """
        path = self.processed_dir / "inspired_dialogs.csv"
        if not path.exists():
            logger.info("[UserEmbedding] inspired_dialogs.csv not found, skipping INSPIRED.")
            return pd.DataFrame(columns=["user_id", "text_profile"])

        df = pd.read_csv(path)
        required = {"dialog_id", "speaker", "text"}
        if not required.issubset(df.columns):
            logger.warning(
                "[UserEmbedding] inspired_dialogs.csv missing required columns "
                f"{required - set(df.columns)}. Skipping INSPIRED."
            )
            return pd.DataFrame(columns=["user_id", "text_profile"])

        grouped = df.groupby(["dialog_id", "speaker"])["text"].apply(
            lambda xs: " ".join(str(t) for t in xs if isinstance(t, str))
        )
        profiles = grouped.reset_index()
        profiles["user_id"] = (
            "inspired:" + profiles["dialog_id"].astype(str) + ":" + profiles["speaker"].astype(str)
        )
        profiles = profiles.rename(columns={"text": "text_profile"}) if "text" in profiles.columns else profiles
        profiles = profiles.rename(columns={0: "text_profile"}) if 0 in profiles.columns else profiles

        if "text_profile" not in profiles.columns:
            profiles["text_profile"] = grouped.values

        return profiles[["user_id", "text_profile"]]

    def _build_redial_text_profiles(self) -> pd.DataFrame:
        """
        redial_dialogues.csv:
          dialog_id,split,utterance_index,speaker_id,text,...
        """
        path = self.processed_dir / "redial_dialogues.csv"
        if not path.exists():
            logger.info("[UserEmbedding] redial_dialogues.csv not found, skipping ReDial.")
            return pd.DataFrame(columns=["user_id", "text_profile"])

        df = pd.read_csv(path)
        required = {"speaker_id", "text"}
        if not required.issubset(df.columns):
            logger.warning(
                "[UserEmbedding] redial_dialogues.csv missing required columns "
                f"{required - set(df.columns)}. Skipping ReDial."
            )
            return pd.DataFrame(columns=["user_id", "text_profile"])

        grouped = df.groupby("speaker_id")["text"].apply(
            lambda xs: " ".join(str(t) for t in xs if isinstance(t, str))
        )
        profiles = grouped.reset_index()
        profiles["user_id"] = "redial:" + profiles["speaker_id"].astype(str)
        profiles = profiles.rename(columns={"text": "text_profile"}) if "text" in profiles.columns else profiles
        profiles = profiles.rename(columns={0: "text_profile"}) if 0 in profiles.columns else profiles

        if "text_profile" not in profiles.columns:
            profiles["text_profile"] = grouped.values

        return profiles[["user_id", "text_profile"]]

    def _build_text_user_embeddings(self) -> pd.DataFrame:
        """
        from ccpe_dialogue.csv, inspired_dialogs.csv, redial_dialogues.csv,
        collect user dialoge text, then create text-based user embedding.

        return:
          user_id (str), embedding_text (list[float])
        """
        if not self.config.use_text:
            logger.info("[UserEmbedding] use_text=False → skipping text-based user embeddings.")
            return pd.DataFrame(columns=["user_id", "embedding_text"])

        # 1) create user text profile from each source
        dfs: List[pd.DataFrame] = []
        dfs.append(self._build_ccpe_text_profiles())
        dfs.append(self._build_inspired_text_profiles())
        dfs.append(self._build_redial_text_profiles())

        profiles_all = pd.concat(dfs, ignore_index=True)
        profiles_all = profiles_all.dropna(subset=["text_profile"])

        if profiles_all.empty:
            logger.info("[UserEmbedding] No text profiles found. Skipping text embeddings.")
            return pd.DataFrame(columns=["user_id", "embedding_text"])

        # 2) text -> embedding
        texts = profiles_all["text_profile"].tolist()
        logger.info(f"[UserEmbedding] Encoding {len(texts)} text-based user profiles")

        vecs = self.embedder.embed_texts(texts)
        if len(vecs) != len(texts):
            raise RuntimeError(
                f"[UserEmbedding] embedder returned {len(vecs)} vectors for {len(texts)} texts"
            )

        profiles_all["embedding_text"] = [v for v in vecs]

        logger.info(
            f"[UserEmbedding] Built text-based embeddings for "
            f"{profiles_all['user_id'].nunique()} users (dialog/profile-ids)"
        )

        return profiles_all[["user_id", "embedding_text"]]

    # ---------- Step 3: rating + text α-mixing & save ----------

    def build_user_embeddings(self, out_path: Path) -> pd.DataFrame:
        """
        overall user embedding pipeline:

          1) rating based embedding_rating
          2) (option) dialogue text based embedding_text
          3) α * rating + (1-α) * text 로 mix → embedding (final)
        """
        # 1) rating based
        df_rating = self._build_rating_user_embeddings()

        # 2) text based
        df_text = self._build_text_user_embeddings()

        # 3) merge (outer join: rating-only, text-only)
        if df_text.empty:
            df_merged = df_rating.copy()
            df_merged["embedding_text"] = None
        else:
            df_merged = pd.merge(
                df_rating,
                df_text,
                on="user_id",
                how="outer",
            )

        # rating-only / text-only case fill
        if "embedding_rating" not in df_merged.columns:
            df_merged["embedding_rating"] = None
        if "num_movies" not in df_merged.columns:
            df_merged["num_movies"] = 0
        df_merged["num_movies"] = df_merged["num_movies"].fillna(0).astype(int)

        # 4) α-mixing: final = α * rating + (1-α) * text
        alpha = self.config.mix_alpha
        final_vecs: List[Optional[List[float]]] = []

        for _, row in df_merged.iterrows():
            r_vec = row.get("embedding_rating")
            t_vec = row.get("embedding_text")

            r = np.array(r_vec, dtype=np.float32) if isinstance(r_vec, list) else None
            t = np.array(t_vec, dtype=np.float32) if isinstance(t_vec, list) else None

            if r is not None and t is not None:
                if r.shape == t.shape:
                    final = alpha * r + (1.0 - alpha) * t
                else:
                    logger.warning(
                        f"[UserEmbedding] Dim mismatch for user_id={row.get('user_id')}, "
                        f"rating_dim={r.shape}, text_dim={t.shape}. "
                        f"Using rating_vec only."
                    )
                    final = r
                final_vecs.append(final.tolist())
            elif r is not None:
                final_vecs.append(r.tolist())
            elif t is not None:
                final_vecs.append(t.tolist())
            else:
                final_vecs.append(None)

        df_merged["embedding"] = final_vecs

        df_out = df_merged[
            ["user_id", "embedding", "embedding_rating", "embedding_text", "num_movies"]
        ]

        out_path.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_parquet(out_path, index=False)
        logger.info(
            f"[UserEmbedding] Saved {len(df_out)} user embeddings to {out_path}"
        )

        return df_out
