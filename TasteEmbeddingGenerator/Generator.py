# TasteEmbeddingGenerator/Generator.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
from typing import Literal, Optional

import logging

from .embeddings_backend import (
    BaseEmbeddingBackend,
    OpenAIEmbeddingBackend, 
    SentenceTransformerBackend,
)
from .MovieEmbedding import MovieEmbeddingConfig, MovieEmbeddingGenerator
from .UserEmbedding import UserEmbeddingConfig, UserEmbeddingGenerator

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

EmbeddingBackendType = Literal["openai", "sentence-transformers"]


@dataclass
class TasteEmbeddingConfig:
    project_root: Path
    backend_type: EmbeddingBackendType = "sentence-transformers"
    model_name: str = "BAAI/bge-base-en-v1.5"  # sentence-transformers
    openai_model: str = "text-embedding-3-large"
    movie_sources: list[str] = None
    batch_size: int = 64
    rating_threshold: float = 4.0
    min_movies: int = 3

    def __post_init__(self):
        if self.movie_sources is None:
            self.movie_sources = ["movielens"]


class TasteEmbeddingGenerator:
    """High-level pipeline that builds movie & user taste embeddings."""

    def __init__(self, config: TasteEmbeddingConfig):
        self.config = config
        self.project_root = config.project_root
        self.dataset_processed = self.project_root / "Dataset" / "processed"
        self.artifacts_dir = self.project_root / "TasteEmbeddingGenerator" / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        self.backend: BaseEmbeddingBackend = self._init_backend()
        logger.info(f"[TasteEmbedding] Using backend={type(self.backend).__name__}")

    def _init_backend(self) -> BaseEmbeddingBackend:
        if self.config.backend_type == "openai":
            return OpenAIEmbeddingBackend(model=self.config.openai_model)
        elif self.config.backend_type == "sentence-transformers":
            return SentenceTransformerBackend(model_name=self.config.model_name)
        else:
            raise ValueError(f"Unknown backend_type: {self.config.backend_type}")

    # ---------- End-to-end steps ----------

    def build_movie_embeddings(self, limit: Optional[int] = None) -> Path:
        movie_emb_path = self.artifacts_dir / "movie_embeddings.parquet"

        mcfg = MovieEmbeddingConfig(
            processed_dir=self.dataset_processed,
            backend=self.backend,
            batch_size=self.config.batch_size,
            sources=self.config.movie_sources,
        )
        mg = MovieEmbeddingGenerator(mcfg)
        mg.build_embeddings(movie_emb_path, limit=limit)

        return movie_emb_path

    def build_user_embeddings(self, movie_emb_path: Path) -> Path:
        user_emb_path = self.artifacts_dir / "user_embeddings.parquet"

        ucfg = UserEmbeddingConfig(
            processed_dir=self.dataset_processed,
            movie_embedding_path=movie_emb_path,
            embedder=self.backend,            # sentence-transformers / OpenAI
            rating_threshold=self.config.rating_threshold,
            min_movies=self.config.min_movies,
            source_filter="movielens",        # rating - movielens based
            use_text=True,                    # ccpe / inspired / redial text use
            mix_alpha=0.7,                    # tuning α value
        )
        ug = UserEmbeddingGenerator(ucfg)
        ug.build_user_embeddings(user_emb_path)

        return user_emb_path

    def run_full_pipeline(self, movie_limit: Optional[int] = None):
        """Convenience function to run everything at once."""
        logger.info("[TasteEmbedding] Step 1: Building movie embeddings")
        movie_emb_path = self.build_movie_embeddings(limit=movie_limit)

        logger.info("[TasteEmbedding] Step 2: Building user embeddings")
        user_emb_path = self.build_user_embeddings(movie_emb_path)

        logger.info(
            f"[TasteEmbedding] Done. Movie embeddings: {movie_emb_path}, "
            f"User embeddings: {user_emb_path}"
        )


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]

    cfg = TasteEmbeddingConfig(
        project_root=project_root,
        # backend_type="sentence-transformers",       # OR "openai"
        backend_type="openai",
        model_name="BAAI/bge-base-en-v1.5",         # BGE
        openai_model="text-embedding-3-large",      # OpenAI
        movie_sources=["movielens", "movietweetings", "inspired"],
        batch_size=64,
        rating_threshold=4.0,
        min_movies=3,
    )

    gen = TasteEmbeddingGenerator(cfg)

    # case1) when running full pipeline (movie embedding + user embedding)
    # gen.run_full_pipeline(movie_limit=None)

    # case2) when running only user embedding (movie embedding already exists)
    movie_emb_path = (
        project_root
        / "TasteEmbeddingGenerator"
        / "artifacts"
        / "movie_embeddings.parquet"
    )

    user_emb_path = gen.build_user_embeddings(movie_emb_path)

    logger.info(f"[TasteEmbedding] Done. User embeddings: {user_emb_path}")

