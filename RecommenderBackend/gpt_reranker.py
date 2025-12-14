# RecommenderBackend/gpt_reranker.py

"""
GPT-based preference reranker for movie recommendations.

Used on top of embedding-based retrieval in recommender.py.

- predict_like_score(user_profile_text, movie_meta) -> score 1–5
- combined_score(user_vec, movie_vec, gpt_score, alpha) -> final scalar
"""

from typing import Dict, Any

import numpy as np
from openai import OpenAI

client = OpenAI()

# Replace this with the actual fine-tuned model id once you have it
FINE_TUNED_MODEL = "ft:gpt-4o-mini-2024-07-18:org:project:movie-pref-ranker"


def predict_like_score(user_profile: str, movie_meta: Dict[str, Any]) -> float:
    """
    Call the fine-tuned GPT model to predict how much the user
    will like this movie on a 1–5 scale.
    """
    title = movie_meta.get("title") or movie_meta.get("movie_title", "Unknown Title")
    genres = movie_meta.get("genres") or movie_meta.get("movie_genres", [])
    if isinstance(genres, list):
        genres_str = ", ".join(genres)
    else:
        genres_str = str(genres)
    overview = movie_meta.get("overview") or movie_meta.get("plot", "")

    prompt = f"""User profile:
{user_profile}

Candidate movie:
Title: {title}
Genres: {genres_str}
Plot: {overview}

Question: Based on the user's tastes and the movie description,
how much is this user likely to enjoy this movie on a 1-5 scale?
Answer with a SINGLE number from 1 to 5.
"""

    resp = client.chat.completions.create(
        model=FINE_TUNED_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise movie preference predictor. Answer with a single number 1-5.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    raw = resp.choices[0].message.content.strip()
    try:
        return float(raw)
    except ValueError:
        # Fallback if model replies weirdly
        return 3.0


def combined_score(
    user_vec: np.ndarray,
    movie_vec: np.ndarray,
    gpt_score: float,
    alpha: float = 0.7,
) -> float:
    """
    Combine cosine similarity between user_vec and movie_vec with
    the GPT 1–5 pref score.

    - alpha: weight for cosine similarity
    - (1 - alpha): weight for GPT score
    """
    # cosine sim in [-1, 1]; we'll bound to [0, 1] for clarity
    sim = float(user_vec @ movie_vec)
    sim = max(0.0, min(1.0, sim))

    # normalize GPT 1–5 into [0, 1]
    gpt_norm = (gpt_score - 1.0) / 4.0
    gpt_norm = max(0.0, min(1.0, gpt_norm))

    return alpha * sim + (1.0 - alpha) * gpt_norm
