"""
TasteEmbeddingGenerator package

Provides:
    - Embedding backend interfaces (OpenAI, SentenceTransformer)
    - MovieEmbedding and UserEmbedding generators
    - High-level TasteEmbeddingGenerator pipeline
"""

from .embeddings_backend import (
    BaseEmbeddingBackend,
    OpenAIEmbeddingBackend,
    SentenceTransformerBackend,
)

from .MovieEmbedding import (
    MovieEmbeddingConfig,
    MovieEmbeddingGenerator,
)

from .UserEmbedding import (
    UserEmbeddingConfig,
    UserEmbeddingGenerator,
)

from .Generator import (
    TasteEmbeddingConfig,
    TasteEmbeddingGenerator,
)

__all__ = [
    # backends
    "BaseEmbeddingBackend",
    "OpenAIEmbeddingBackend",
    "SentenceTransformerBackend",

    # movie embedding
    "MovieEmbeddingConfig",
    "MovieEmbeddingGenerator",

    # user embedding
    "UserEmbeddingConfig",
    "UserEmbeddingGenerator",

    # full pipeline
    "TasteEmbeddingConfig",
    "TasteEmbeddingGenerator",
]
