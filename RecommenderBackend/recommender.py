from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Dict, List

import numpy as np

from embedding_loader import load_movie_embeddings
from vector_index import MovieIndex
from llm import call_llm
from config import MOVIE_EMBED_PATH, TOP_K, FINAL_K
from user_store import load_user_state, save_user_state
from gpt_reranker import predict_like_score, combined_score

# -------------------------------------------------------------------
# Make TasteEmbeddingGenerator importable (sibling directory)
# -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from TasteEmbeddingGenerator.embeddings_backend import SentenceTransformerBackend
from openai import OpenAI


# -------------------------------------------------------------------
# Embedding backend (SentenceTransformer for taste vectors)
# -------------------------------------------------------------------

EMBED_MODEL_NAME = "BAAI/bge-base-en-v1.5"

_backend = SentenceTransformerBackend(
    model_name=EMBED_MODEL_NAME,
    device="mps",  # "mps" for your Mac; use "cpu" or "cuda" elsewhere
)


def embed_user_taste(text: str) -> np.ndarray:
    """
    Convert a normalized taste description into a unit-norm embedding
    using the same backbone as movie embeddings (BGE-base).
    """
    vec = _backend.embed_texts([text])[0]
    vec = np.asarray(vec, dtype=np.float32)

    # Normalize so cosine similarity ≈ dot product
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec


# -------------------------------------------------------------------
# Optional: LLM-based taste normalization (minimize noisy input)
# -------------------------------------------------------------------

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_taste_with_llm(user_input: str) -> str:
    """
    Uses an LLM to convert raw user input into a clean taste profile string.
    This can reduce noise and make embeddings more stable.

    NOTE: This is an extra GPT call. If you want to avoid it,
    just use the raw user_input as the taste profile.
    """
    system_prompt = """
You are a preference extraction assistant for a movie recommender system.
Your job is to rewrite the user's input as a clean, concise taste profile.
Do NOT recommend movies.
Only return the normalized preference description.
"""

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0.2,
    )

    return resp.choices[0].message.content.strip()


# -------------------------------------------------------------------
# Load movie embeddings & build index
# -------------------------------------------------------------------

movie_embeddings, movie_metadata = load_movie_embeddings(MOVIE_EMBED_PATH)
movie_index = MovieIndex(movie_embeddings)

# -------------------------------------------------------------------
# Persistent runtime users (REAL users only, not offline dataset users)
# user_vectors: user_id -> taste vector (np.ndarray)
# -------------------------------------------------------------------

user_vectors: Dict[str, np.ndarray] = load_user_state()
USER_FUSE_ALPHA = 0.8  # 0.8 old taste, 0.2 new taste per interaction

# In-process textual history for nicer explanations (not persisted)
preference_history: Dict[str, List[str]] = {}


# -------------------------------------------------------------------
# Core recommender entry point
# -------------------------------------------------------------------

# def recommend(user_input: str, user_id: Optional[str] = None) -> str:
#     """
#     Main recommendation entry point.

#     Steps:
#     1. Convert this message into a taste embedding (optionally via LLM normalization).
#     2. If user_id is known, fuse with previous taste embedding (EMA).
#     3. Persist updated taste vector to runtime_users.parquet (via user_store).
#     4. Maintain a small preference text history per user for explanations.
#     5. Retrieve Top-K movies via embedding index.
#     6. Use a single LLM call to rerank & explain FINAL_K movies.
#     """

#     # ----------------- 1) TASTE EMBEDDING FROM CURRENT INPUT -----------------
#     # Option A (cheaper): directly embed the raw input
#     taste_profile = user_input

#     # Option B (more structured): uncomment to normalize via GPT
#     # taste_profile = extract_taste_with_llm(user_input)

#     new_vec = embed_user_taste(taste_profile)

#     # ----------------- 2) FUSE WITH PREVIOUS TASTE (IF ANY) ------------------
#     has_identity = user_id is not None and user_id != ""

#     if has_identity and user_id in user_vectors:
#         prev_vec = user_vectors[user_id]
#         user_vec = USER_FUSE_ALPHA * prev_vec + (1.0 - USER_FUSE_ALPHA) * new_vec
#     else:
#         user_vec = new_vec

#     # ----------------- 3) UPDATE & PERSIST USER STATE ------------------------
#     if has_identity:
#         # Vector memory
#         user_vectors[user_id] = user_vec
#         save_user_state(user_vectors)

#         # Textual preference history (for LLM explanations only)
#         prefs = preference_history.get(user_id, [])
#         prefs.append(user_input)
#         # keep last N messages for sanity
#         if len(prefs) > 10:
#             prefs = prefs[-10:]
#         preference_history[user_id] = prefs
#         history_text = "\n".join(f"- {p}" for p in prefs)
#     else:
#         history_text = "- (no persistent user id; only using this message)"

#     # ----------------- 4) MOVIE RETRIEVAL ------------------------------------
#     # If MovieIndex expects (1, d), wrap with user_vec[None, :]
#     idxs, scores = movie_index.search(user_vec, k=TOP_K)
#     candidates = [movie_metadata[i] for i in idxs]

#     # ----------------- 5) LLM RERANK + EXPLANATION ---------------------------
#     rerank_prompt = f"""
# You are a movie recommender system.

# User's long-term preferences so far:
# {history_text}

# User's latest message:
# {user_input}

# Candidate movies (as a Python-like list of dicts):
# {candidates}

# From these candidates, choose the best {FINAL_K} movies
# that match BOTH the user's long-term tastes and their latest message.
# Explain briefly why each one fits.
# Return a clear, human-readable list.
# """

#     return call_llm(rerank_prompt, temperature=0.4)


# ----------------- PERSISTENT USER STATE & LOGGING -----------------

from typing import Optional, Dict
import json
from datetime import datetime
from pathlib import Path
import numpy as np

from user_store import load_user_state, save_user_state

# Persistent runtime users: user_id -> np.ndarray taste vector
user_vectors: Dict[str, np.ndarray] = load_user_state()
USER_FUSE_ALPHA = 0.8  # 0.8 old taste, 0.2 new

# In-process text memory for explanations
preference_history: dict[str, list[str]] = {}

# Recommendation log path (JSON Lines)
RECOMMENDER_LOG_PATH = Path(__file__).parent / "rec_log.jsonl"


def _init_message_counts_from_log() -> Dict[str, int]:
    """
    Scan rec_log.jsonl (if it exists) and recover the highest msg_index
    per user_id so that new messages continue the sequence.
    """
    counts: Dict[str, int] = {}
    if not RECOMMENDER_LOG_PATH.exists():
        return counts

    try:
        with open(RECOMMENDER_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                uid = rec.get("user_id")
                mi = rec.get("msg_index")
                if uid is None or mi is None:
                    continue
                try:
                    mi = int(mi)
                except (TypeError, ValueError):
                    continue
                prev = counts.get(uid, 0)
                if mi > prev:
                    counts[uid] = mi
    except Exception as e:
        print(f"[recommender] Warning: could not parse log {RECOMMENDER_LOG_PATH}: {e}")
    return counts


# Per-user message counters for "msg 1, msg 2, …"
USER_MESSAGE_COUNTS: Dict[str, int] = _init_message_counts_from_log()


def _next_msg_index(user_id: str) -> int:
    cur = USER_MESSAGE_COUNTS.get(user_id, 0) + 1
    USER_MESSAGE_COUNTS[user_id] = cur
    return cur


def log_recommendation(
    *,
    user_id: str,
    msg_index: int,
    user_input: str,
    history_text: str,
    user_vec: np.ndarray,
    candidate_indices: np.ndarray,
    candidate_scores: np.ndarray,
    final_k: int,
) -> None:
    """
    Append a single recommendation event to rec_log.jsonl.

    This gives you:
      - exact query
      - message order per user (msg_index)
      - fused taste vector used for retrieval
      - which movie indices were retrieved (Top-K)
      - the number of movies LLM was asked to focus on (final_k)
    """
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": user_id,
        "msg_index": msg_index,
        "user_input": user_input,
        "history_text": history_text,
        "user_vec": user_vec.tolist(),  # store as list[float]
        "candidate_indices": [int(i) for i in candidate_indices.tolist()],
        "candidate_scores": [float(s) for s in candidate_scores.tolist()],
        "final_k": int(final_k),
    }

    try:
        with open(RECOMMENDER_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"[recommender] Warning: failed to write log: {e}")


# ----------------- CORE RECOMMENDER -----------------


def recommend(user_input: str, user_id: Optional[str] = None) -> str:
    """
    Main recommendation entry point.

    - Build a taste vector from this input
    - Fuse with previous taste if user_id is known
    - Save updated taste vector to runtime_users.parquet
    - Keep a small text history per user for the LLM
    - Retrieve movies and ask GPT to explain/rerank using both history + latest input
    - Log each interaction to rec_log.jsonl with msg_index, query, and rec indices
    """

    # ----------------- 1) TASTE EMBEDDING FROM CURRENT INPUT -----------------
    # Simple version: use raw input as taste profile
    # Option A (cheaper): directly embed the raw input
    taste_profile = user_input

    # Option B (more structured): uncomment to normalize via GPT
    # taste_profile = extract_taste_with_llm(user_input)
    new_vec = embed_user_taste(taste_profile)
    new_vec = np.array(new_vec, dtype=np.float32)

    # ----------------- 2) FUSE WITH PREVIOUS TASTE (IF ANY) ------------------
    has_identity = user_id is not None and user_id != ""

    if has_identity and user_id in user_vectors:
        prev_vec = user_vectors[user_id]
        user_vec = USER_FUSE_ALPHA * prev_vec + (1.0 - USER_FUSE_ALPHA) * new_vec
    else:
        user_vec = new_vec

    # Normalize fused vector for safety
    norm = np.linalg.norm(user_vec)
    if norm > 0:
        user_vec = user_vec / norm

    # ----------------- 3) UPDATE & PERSIST USER STATE ------------------------
    if has_identity:
        # Vector memory
        user_vectors[user_id] = user_vec
        save_user_state(user_vectors)

        # Textual preference history (for LLM explanations)
        prefs = preference_history.get(user_id, [])
        prefs.append(user_input)
        # Optional: keep only last N preference lines
        if len(prefs) > 10:
            prefs = prefs[-10:]
        preference_history[user_id] = prefs
        history_text = "\n".join(f"- {p}" for p in prefs)
    else:
        history_text = "- (no stable user id; only using this message)"

    # ----------------- 4) MOVIE RETRIEVAL ------------------------------------
    # NOTE: movie_index.search should accept user_vec (D,) or (1, D)
    idxs, scores = movie_index.search(user_vec, k=TOP_K)
        # idxs, scores = movie_index.search(user_vec, k=TOP_K)
    # idxs = np.asarray(idxs).ravel()
    # scores = np.asarray(scores).ravel()

    # # Build candidate list with combined scores
    # scored = []
    # for idx, base_score in zip(idxs, scores):
    #     movie = movie_metadata[idx]
    #     gpt_score = predict_like_score(history_text, movie)  # or user_input
    #     final_score = combined_score(user_vec, movie_embeddings[idx], gpt_score)
    #     scored.append((final_score, movie))

    # # Sort and keep FINAL_K
    # scored.sort(key=lambda x: x[0], reverse=True)
    # top_movies = [m for _, m in scored[:FINAL_K]]

    # Make sure these are 1D arrays
    idxs = np.asarray(idxs)
    scores = np.asarray(scores)
    if idxs.ndim > 1:
        idxs = idxs[0]
    if scores.ndim > 1:
        scores = scores[0]

    rec_indices = idxs[:FINAL_K]
    candidates = [movie_metadata[i] for i in idxs]

    # ----------------- 5) LOG THIS RECOMMENDATION EVENT ----------------------
    if has_identity:
        msg_index = _next_msg_index(user_id)
        log_recommendation(
            user_id=user_id,
            msg_index=msg_index,
            user_input=user_input,
            history_text=history_text,
            user_vec=user_vec,
            candidate_indices=idxs,
            candidate_scores=scores,
            final_k=FINAL_K,
        )
    # If no user_id, we skip logging (ephemeral session)

    # ----------------- 6) LLM RERANK + EXPLANATION ---------------------------
    rerank_prompt = f"""
You are a movie recommender system.

User's long-term preferences so far:
{history_text}

User's latest message:
{user_input}

Candidate movies (as a Python-like list of dicts):
{candidates}

From these candidates, choose the best {FINAL_K} movies
that match BOTH the user's long-term tastes and their latest message.
Explain briefly why each one fits.
Return a clear, human-readable list.
"""

    return call_llm(rerank_prompt, temperature=0.4)

