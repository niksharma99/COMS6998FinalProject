# TasteEmbeddingGenerator/MovieEmbedding.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional

import logging
import pandas as pd

from .embeddings_backend import BaseEmbeddingBackend

logger = logging.getLogger(__name__)

MOVIE_SOURCE = Literal["movielens", "movietweetings", "inspired"]


@dataclass
class MovieEmbeddingConfig:
    processed_dir: Path
    backend: BaseEmbeddingBackend
    batch_size: int = 64
    sources: List[MOVIE_SOURCE] | None = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = ["movielens"]


class MovieEmbeddingGenerator:
    """
    Build movie embeddings from TMDB-enriched movie tables.

    - source: movielens, movietweetings, inspired
    - duplicates handling:
        for same tmdb_id movie, map to same embedding vector.
        (if not tmdb_id, source+movie_id combination fallback)
    """

    def __init__(self, config: MovieEmbeddingConfig):
        self.config = config
        self.processed_dir = config.processed_dir
        self.backend = config.backend

    # ---------- data loading ----------

    def _load_movies_movielens(self) -> pd.DataFrame:
        """
        Columns (after enrich):
          movieId,title,genres,year,
          tmdb_id,tmdb_title,tmdb_release_date,tmdb_overview,
          tmdb_runtime,tmdb_genres,tmdb_top_cast,tmdb_keywords
        """
        path = self.processed_dir / "movielens_movies_tmdb.csv"
        df = pd.read_csv(path)
        df["source"] = "movielens"
        df.rename(columns={"movieId": "movie_id"}, inplace=True)
        return df

    def _load_movies_movietweetings(self) -> pd.DataFrame:
        """
        Columns:
          movie_id,raw_title,genres,title,year,
          tmdb_id,tmdb_title,tmdb_release_date,tmdb_overview,
          tmdb_runtime,tmdb_genres,tmdb_top_cast,tmdb_keywords
        """
        path = self.processed_dir / "movietweetings_movies_tmdb.csv"
        df = pd.read_csv(path)
        df["source"] = "movietweetings"
    
        if "movie_id" not in df.columns:
            raise ValueError(
                "[MovieEmbedding] movietweetings_movies_tmdb.csv must contain 'movie_id' column."
            )
        return df

    def _load_movies_inspired(self) -> pd.DataFrame:
        """
        Columns (tmdb enrich 후):
          title,year,trailer_duration,actors,awards,box_office,country,
          director,dvd_release,genre,imdb_id,imdb_type,imdb_votes,language,
          long_plot,movie_runtime,poster,production,rated,rating,release_date,
          short_plot,video_id,writer,youtube_comment,youtube_dislike,
          youtube_favorite,youtube_like,youtube_link,youtube_view,
          tmdb_id,tmdb_title,tmdb_release_date,tmdb_overview,
          tmdb_runtime,tmdb_genres,tmdb_top_cast,tmdb_keywords
        """
        path = self.processed_dir / "inspired_movie_database_tmdb.csv"
        df = pd.read_csv(path)
        df["source"] = "inspired"

        if "movie_id" not in df.columns:
            if "tmdb_id" in df.columns:
                def _safe_int(x):
                    try:
                        return int(x)
                    except Exception:
                        return pd.NA

                df["movie_id"] = df["tmdb_id"].map(_safe_int)
                if df["movie_id"].isna().all():
                    df["movie_id"] = df.index
            else:
                df["movie_id"] = df.index

        return df

    def load_all_sources(self) -> pd.DataFrame:
        dfs: List[pd.DataFrame] = []
        for src in self.config.sources:
            if src == "movielens":
                dfs.append(self._load_movies_movielens())
            elif src == "movietweetings":
                dfs.append(self._load_movies_movietweetings())
            elif src == "inspired":
                dfs.append(self._load_movies_inspired())
            else:
                raise ValueError(f"Unknown movie source: {src}")

        df_all = pd.concat(dfs, ignore_index=True)
        logger.info(
            f"[MovieEmbedding] Loaded movies from {self.config.sources}: {df_all.shape}"
        )
        return df_all

    # ---------- text building ----------

    @staticmethod
    def build_movie_text(row: pd.Series) -> str:
        """
        Create a rich textual description of a movie from available columns.
        Use TMDB info first, then use source-specific column if not sufficient
        """
        source = row.get("source", "")

        # ---- title & year ----
        title = row.get("tmdb_title") or row.get("title") or row.get("raw_title") or ""
        year = ""
        if "year" in row and pd.notna(row["year"]):
            try:
                year = str(int(row["year"]))
            except Exception:
                year = str(row["year"])
        elif "tmdb_release_date" in row and isinstance(row["tmdb_release_date"], str):
            year = row["tmdb_release_date"][:4]

        # ---- genres ----
        genres = row.get("tmdb_genres") or row.get("genres") or row.get("genre") or ""

        # ---- overview / plot ----
        overview = row.get("tmdb_overview") or ""
        if not overview and source == "inspired":
            overview = row.get("long_plot") or row.get("short_plot") or ""

        # ---- cast / actors ----
        cast = row.get("tmdb_top_cast") or ""
        if not cast and source == "inspired":
            cast = row.get("actors") or ""

        # ---- director, keywords add (if possible) ----
        director = ""
        if source == "inspired":
            director = row.get("director") or ""

        keywords = row.get("tmdb_keywords") or ""

        parts: List[str] = []
        if title:
            if year:
                parts.append(f"Title: {title} ({year}).")
            else:
                parts.append(f"Title: {title}.")
        if genres:
            parts.append(f"Genres: {genres}.")
        if director:
            parts.append(f"Director: {director}.")
        if overview:
            parts.append(f"Plot: {overview}")
        if cast:
            parts.append(f"Cast: {cast}.")
        if keywords:
            parts.append(f"Keywords: {keywords}.")

        text = " ".join(p.strip() for p in parts if p)
        return text

    @staticmethod
    def _make_embed_key(row: pd.Series) -> str:
        """
        duplicate handling
        """
        tmdb_id = row.get("tmdb_id")
        source = row.get("source", "unknown")
        movie_id = row.get("movie_id")

        if pd.notna(tmdb_id):
            try:
                return f"tmdb:{int(tmdb_id)}"
            except Exception:
                return f"tmdb:{str(tmdb_id)}"

        return f"{source}:{movie_id}"

    # ---------- embedding & save ----------

    def build_embeddings(
        self,
        out_path: Path,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Compute movie embeddings and save to a parquet file.

        out_path: e.g. TasteEmbeddingGenerator/artifacts/movie_embeddings.parquet
        """
        df = self.load_all_sources()

        if limit is not None:
            df = df.head(limit).copy()
            logger.info(f"[MovieEmbedding] Limiting to first {limit} movies")

        # 1) text
        df["embedding_text"] = df.apply(self.build_movie_text, axis=1)

        # 2) duplicate movie key
        df["embed_key"] = df.apply(self._make_embed_key, axis=1)

        # 3) unique text set based on embed_key
        uniq = df[["embed_key", "embedding_text"]].drop_duplicates("embed_key")
        uniq_texts = uniq["embedding_text"].tolist()
        uniq_keys = uniq["embed_key"].tolist()

        total_unique = len(uniq_texts)
        logger.info(
            f"[MovieEmbedding] Found {total_unique} unique movies to encode "
            f"(from {len(df)} rows)"
        )

        # 4) for unique text, calculate embeddings in batches
        embeddings_list: List[List[float]] = []
        batch_size = self.config.batch_size

        for start in range(0, total_unique, batch_size):
            end = min(start + batch_size, total_unique)
            batch = uniq_texts[start:end]
            vecs = self.backend.embed_texts(batch)
            if len(vecs) != len(batch):
                raise RuntimeError(
                    f"Embedding backend returned {len(vecs)} vectors for {len(batch)} texts"
                )
            embeddings_list.extend(vecs)
            logger.info(f"[MovieEmbedding] Encoded {end}/{total_unique} unique movies")

        # 5) embed_key -> embedding mapping
        key_to_vec = {k: v for k, v in zip(uniq_keys, embeddings_list)}

        # 6) attach embeddings back to full df
        df["embedding"] = df["embed_key"].map(key_to_vec)

        # 🔧 FIX: unify 'year' dtype before saving (mixed str/int → ArrowInvalid)
        if "year" in df.columns:
            df["year"] = (
                pd.to_numeric(df["year"], errors="coerce")  # "2020" → 2020, bad values → NaN
                  .astype("Int64")                           # pandas nullable int
            )

        for col in df.columns:
            if col in ("embedding", "embedding_text"):
                continue
            if df[col].dtype == "object":
                df[col] = df[col].astype("string")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_path, index=False)
        logger.info(
            f"[MovieEmbedding] Saved embeddings to {out_path} (shape={df.shape})"
        )

        return df
