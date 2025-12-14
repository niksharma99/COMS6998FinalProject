#!/usr/bin/env python3
# RecommenderBackend/letterboxd_to_finetune.py

"""
Convert letterboxd_dataset.jsonl into OpenAI chat fine-tuning data.

Input:
  - letterboxd_dataset.jsonl (from letterboxd_collect_dataset.py)
    Each line: {
      "member_lid": str,
      "username": str,
      "n_entries": int,
      "favorites_top4": [LogEntrySimplified, ...],
      "rating_history": [LogEntrySimplified, ...]
    }

Output:
  - artifacts/movie_pref_train.jsonl
  - artifacts/movie_pref_val.jsonl

Each fine-tune example is:
  System: "You are a precise movie preference predictor."
  User:   user_profile + candidate movie details
  Assistant: a single integer 1-5 (the user's rating)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

LETTERBOXD_PATH = ROOT / "letterboxd_dataset.jsonl"
TRAIN_OUT = ARTIFACTS / "movie_pref_train.jsonl"
VAL_OUT = ARTIFACTS / "movie_pref_val.jsonl"


def load_letterboxd_dataset(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def build_user_profile(user: Dict[str, Any]) -> str:
    """
    Construct a pseudo-natural language taste profile from:
    - favorites_top4
    - rating_history (high- vs low-rated)

    This is what you can describe in the talk:
    "We treat each user's top 4 highest-rated films as favorites and summarize
     other high/low ratings and reviews into a text taste profile."
    """
    username = user.get("username", "UnknownUser")

    favs = user.get("favorites_top4", []) or []
    fav_titles = [e.get("film_title") for e in favs if e.get("film_title")]
    fav_titles = [t for t in fav_titles if t]

    # Split rating history into liked vs disliked based on rating threshold
    hist = user.get("rating_history", []) or []
    liked = []
    disliked = []
    for e in hist:
        r = e.get("rating")
        title = e.get("film_title")
        if title is None or r is None:
            continue
        try:
            r_float = float(r)
        except (TypeError, ValueError):
            continue
        if r_float >= 4.0:
            liked.append(title)
        elif r_float <= 2.0:
            disliked.append(title)

    # Deduplicate & truncate for sanity
    fav_titles = list(dict.fromkeys(fav_titles))[:4]
    liked = [t for t in liked if t not in fav_titles]
    liked = list(dict.fromkeys(liked))[:8]
    disliked = list(dict.fromkeys(disliked))[:8]

    lines = []
    lines.append(f"User: {username}")
    if fav_titles:
        lines.append("Top 4 favorite films:")
        lines.append(", ".join(fav_titles))
    if liked:
        lines.append("\nSome other films they rated highly:")
        lines.append(", ".join(liked))
    if disliked:
        lines.append("\nFilms they did not enjoy:")
        lines.append(", ".join(disliked))

    profile = "\n".join(lines)
    return profile


def make_prompt(user_profile: str, entry: Dict[str, Any]) -> str:
    """
    Build the prompt text for a single user–movie pair.
    """
    title = entry.get("film_title", "Unknown Title")
    year = entry.get("film_year")
    year_str = f" ({year})" if year else ""
    review = entry.get("review_text") or ""

    return f"""User taste profile:
{user_profile}

Candidate movie:
Title: {title}{year_str}
User's review text (if any):
{review}

Question: Based on this user's tastes and their review,
how much does this user enjoy this movie on a 1-5 scale?
Answer with a SINGLE number from 1 to 5.
"""


def make_completion(entry: Dict[str, Any]) -> str:
    rating = entry.get("rating")
    if rating is None:
        return "3"
    try:
        r_float = float(rating)
    except (TypeError, ValueError):
        r_float = 3.0

    # Letterboxd rating is 0.5–5 in 0.5 increments; map to nearest int 1–5
    r_int = int(round(max(1.0, min(5.0, r_float))))
    return str(r_int)


def build_examples(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Flatten letterboxd records into one row per (user, film) rating example.
    """
    examples = []

    for user in rows:
        user_profile = build_user_profile(user)

        for entry in user.get("rating_history", []) or []:
            if entry.get("rating") is None:
                continue

            prompt = make_prompt(user_profile, entry)
            completion = make_completion(entry)

            examples.append(
                {
                    "user_profile": user_profile,
                    "film_title": entry.get("film_title"),
                    "prompt": prompt,
                    "completion": completion,
                }
            )

    return pd.DataFrame(examples)


def write_chat_finetune_jsonl(df: pd.DataFrame, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            record = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a precise movie preference predictor. "
                                   "You must answer with a single integer from 1 to 5.",
                    },
                    {"role": "user", "content": row["prompt"]},
                    {"role": "assistant", "content": row["completion"]},
                ]
            }
            f.write(json.dumps(record) + "\n")


def main():
    if not LETTERBOXD_PATH.exists():
        raise FileNotFoundError(f"{LETTERBOXD_PATH} not found; run letterboxd_collect_dataset.py first.")

    raw_rows = load_letterboxd_dataset(LETTERBOXD_PATH)
    df = build_examples(raw_rows)

    print(f"Built {len(df)} user-movie rating examples from Letterboxd dataset.")

    train_df, val_df = train_test_split(df, test_size=0.1, random_state=42)
    write_chat_finetune_jsonl(train_df, TRAIN_OUT)
    write_chat_finetune_jsonl(val_df, VAL_OUT)

    print(f"Wrote {len(train_df)} train examples to {TRAIN_OUT}")
    print(f"Wrote {len(val_df)} val examples to {VAL_OUT}")


if __name__ == "__main__":
    main()
