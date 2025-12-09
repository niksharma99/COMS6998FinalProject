# TasteEmbeddingGenerator/embeddings_backend.py

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Any

import logging

logger = logging.getLogger(__name__)


class BaseEmbeddingBackend(ABC):
    """Abstract interface for embedding backends.

    Any backend must implement `embed_texts` with the same signature.
    """

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Encode a batch of texts into vectors (list of float lists)."""
        raise NotImplementedError


# -------- OpenAI backend (text-embedding-3-large ..) --------

@dataclass
class OpenAIEmbeddingBackend(BaseEmbeddingBackend):
    """Embedding backend using OpenAI's text-embedding models.

    Requires:
        pip install openai
        and an environment variable: OPENAI_API_KEY
    """

    model: str = "text-embedding-3-large"
    batch_size: int = 64      # ← OpenAI API batch size
    max_chars_per_text: int = 4000    # ← max chars per text input

    _client: Any = field(init=False, repr=False, default=None)

    def _ensure_client(self):
        if self._client is None:
            try:
                from openai import OpenAI  # type: ignore
            except ImportError as e:
                raise ImportError(
                    "openai package is required for OpenAIEmbeddingBackend. "
                    "Install with `pip install openai`."
                ) from e
            self._client = OpenAI()
            logger.info(f"[OpenAIEmbeddingBackend] Initialized with model={self.model}")

    def _truncate(self, text: str) -> str:
        if self.max_chars_per_text is None:
            return text
        text = text or ""
        if len(text) > self.max_chars_per_text:
            return text[: self.max_chars_per_text]
        return text

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using batched OpenAI API calls."""
        self._ensure_client()
        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]

            batch = [self._truncate(t) for t in batch]

            resp = self._client.embeddings.create(
                model=self.model,
                input=batch,
            )
            all_embeddings.extend([d.embedding for d in resp.data])

            logger.info(
                f"[OpenAIEmbeddingBackend] Embedded batch "
                f"{start}–{start + len(batch) - 1} / {len(texts)}"
            )

        return all_embeddings


# -------- SentenceTransformer backend (BGE, GTE, Jina..) --------

@dataclass
class SentenceTransformerBackend(BaseEmbeddingBackend):
    """Embedding backend using sentence-transformers (e.g., BGE, GTE, Jina).

    Example models:
      - 'BAAI/bge-base-en-v1.5'
      - 'thenlper/gte-base'
      - 'jinaai/jina-embeddings-v2-base-en'
    """

    model_name: str = "BAAI/bge-base-en-v1.5"
    device: Optional[str] = None  # e.g. 'cuda', 'mps', 'cpu'

    _model: any = field(init=False, repr=False, default=None)

    def _ensure_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is required for SentenceTransformerBackend. "
                    "Install with `pip install sentence-transformers`."
                ) from e
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(
                f"[SentenceTransformerBackend] Loaded model={self.model_name} on device={self.device}"
            )

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        self._ensure_model()
        if not texts:
            return []
        # encode returns np.ndarray; convert to list of lists
        import numpy as np

        vecs = self._model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,  # cosine similarity
        )
        if isinstance(vecs, list):
            return vecs
        if isinstance(vecs, np.ndarray):
            return vecs.tolist()
        return list(vecs)
