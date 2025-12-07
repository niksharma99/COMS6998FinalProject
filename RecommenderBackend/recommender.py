from taste_parser import extract_structured_taste
from embedding_loader import load_movie_embeddings, load_user_embeddings
from vector_index import MovieIndex
from llm import call_llm
from config import MOVIE_EMBED_PATH, USER_EMBED_PATH, TOP_K, FINAL_K

import numpy as np

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from typing import Dict, Optional
import numpy as np

# Runtime user state (for “real” users during this session)
USER_STATE: Dict[str, dict] = {}



# ------------ LOAD ALL VECTORS -------------
movie_embeddings, movie_metadata = load_movie_embeddings(MOVIE_EMBED_PATH)
user_vectors = load_user_embeddings(USER_EMBED_PATH)

movie_index = MovieIndex(movie_embeddings)

# # ------------ COLD START TASTE EMBEDDING -------------
# def embed_user_taste(text: str) -> np.ndarray:
#     """
#     TEMPORARY: replace with your SentenceTransformer backend
#     """
#     raise NotImplementedError("Plug in your taste embedding model here.")

from TasteEmbeddingGenerator.embeddings_backend import SentenceTransformerBackend
from TasteEmbeddingGenerator.Generator import TasteEmbeddingConfig

# ---- Initialize backend ONCE ----
# _cfg = TasteEmbeddingConfig(
#     backend_type="sentence-transformers",
#     model_name="BAAI/bge-base-en-v1.5"
# )

# _backend = SentenceTransformerBackend(_cfg)

from pathlib import Path
from TasteEmbeddingGenerator.embeddings_backend import SentenceTransformerBackend
from TasteEmbeddingGenerator.Generator import TasteEmbeddingConfig

# ---- Proper project root for your generator ----
GENERATOR_ROOT = Path(__file__).resolve().parents[1] / "TasteEmbeddingGenerator"

_cfg = TasteEmbeddingConfig(
    project_root=str(GENERATOR_ROOT),
    backend_type="sentence-transformers",
    model_name="BAAI/bge-base-en-v1.5"
)

# _backend = SentenceTransformerBackend(_cfg)
_backend = SentenceTransformerBackend(
    model_name=_cfg.model_name,
    device="mps"  # since you're on Mac
)



def embed_user_taste(text: str) -> np.ndarray:
    # vec = _backend.embed_texts([text])[0]
    # return np.array(vec, dtype="float32")
    vec = _backend.embed_texts([text])[0]
    vec = np.array(vec, dtype="float32")
    vec /= np.linalg.norm(vec)
    return vec


# CREATE A USER TASTE VECTOR
def update_user_taste(user_id: Optional[str],
                      taste_profile: str,
                      new_vec: np.ndarray,
                      alpha: float = 0.7) -> tuple[Optional[str], np.ndarray]:
    """
    Update or create a user taste vector.

    - If user_id is None: we don't persist anything (pure cold start).
    - If user_id is new: we store this vector as their initial taste.
    - If user_id exists: we blend old + new (simple EMA).

    Returns: (user_id, fused_vec)
    """
    if user_id is None:
        # Pure cold start: just return the new vector, no persistence
        return None, new_vec

    if user_id not in USER_STATE:
        # First time we see this id
        USER_STATE[user_id] = {
            "taste_vec": new_vec,
            "history_text": taste_profile,
        }
        return user_id, new_vec

    # Refine existing user taste by blending previous + new
    prev_vec = USER_STATE[user_id]["taste_vec"]
    fused = alpha * prev_vec + (1.0 - alpha) * new_vec

    # Re-normalize
    fused /= np.linalg.norm(fused)

    USER_STATE[user_id]["taste_vec"] = fused
    USER_STATE[user_id]["history_text"] += "\n" + taste_profile

    return user_id, fused


# ----------- Get clean taste profile for this user (persistent convo memory stability) -----
from openai import OpenAI
import os

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_taste_with_llm(user_input: str) -> str:
    """
    Uses an LLM to convert raw user input into a clean taste profile string.
    This minimizes prompt noise and standardizes embedding input.
    """

    system_prompt = """
You are a preference extraction assistant for a movie recommender system.
Your job is to rewrite the user's input as a clean, concise taste profile.
Do NOT recommend movies.
Only return the normalized preference description.
"""

    response = _client.chat.completions.create(
        model="gpt-4o-mini",  # cheapest + strong enough
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()




# ------------ CORE RECOMMENDER -----------------
from typing import Optional

def recommend(user_input: str, user_id: Optional[str] = None):


    # ✅ CASE 1: KNOWN USER → USE STORED USER EMBEDDING
    if user_id is not None and user_id in user_vectors:
        user_vec = user_vectors[user_id]

    # ✅ CASE 2: NEW USER → EXTRACT TASTE + EMBED
    else:
        # taste_profile = extract_structured_taste(user_input)
        # user_vec = embed_user_taste(taste_profile)
        taste_profile = extract_taste_with_llm(user_input)
        # taste_profile = user_input
        new_vec = embed_user_taste(taste_profile)

        # Persist or not depending on user_id
        user_id, user_vec = update_user_taste(user_id, taste_profile, new_vec)


    # -------- MOVIE RETRIEVAL ----------
    idxs, scores = movie_index.search(user_vec, k=TOP_K)
    candidates = [movie_metadata[i] for i in idxs]

    # -------- OPTIONAL RERANK ----------
    rerank_prompt = f"""
User query:
{user_input}

Candidate movies:
{candidates}

Select the best {FINAL_K} movies and explain why.
"""

    return call_llm(rerank_prompt, temperature=0.4)
