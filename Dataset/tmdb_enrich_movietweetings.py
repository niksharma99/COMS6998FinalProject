# Dataset/tmdb_enrich_movietweetings.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from tmdb_client import TMDBClient

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "processed"


def normalize_title(title: str) -> str:
    """Normalize movie title string for TMDB search."""
    if not isinstance(title, str):
        return ""
    t = title.strip()
    if "(" in t and t.endswith(")"):
        idx = t.rfind("(")
        t = t[:idx].strip()
    return t


def choose_best_tmdb_match(
    candidates: List[Dict[str, Any]],
    target_year: Optional[int],
) -> Optional[Dict[str, Any]]:
    """Pick the best TMDB match, preferring exact year if available."""
    if not candidates:
        return None

    if target_year is not None:
        for c in candidates:
            rd = c.get("release_date")
            if isinstance(rd, str) and len(rd) >= 4:
                try:
                    y = int(rd[:4])
                except ValueError:
                    continue
                if y == target_year:
                    return c

    # fallback: first candidate
    return candidates[0]


def join_list_of_dicts(
    items: List[Dict[str, Any]],
    key: str,
    top_k: int | None = None,
) -> str:
    names = [it.get(key, "") for it in items if it.get(key)]
    if top_k is not None:
        names = names[:top_k]
    return ", ".join(names)


def enrich_movietweetings_with_tmdb(limit: Optional[int] = None):
    movies_path = PROCESSED_DIR / "movietweetings_movies.csv"
    partial_path = PROCESSED_DIR / "movietweetings_movies_tmdb_partial.csv"

    if partial_path.exists():
        print(f"[INFO] Found partial file: {partial_path}, resuming from it.")
        df = pd.read_csv(partial_path)
    else:
        if not movies_path.exists():
            raise FileNotFoundError(
                f"{movies_path} not found. Run preprocess_movietweetings.py first."
            )
        df = pd.read_csv(movies_path)
        print(f"[INFO] Loaded MovieTweetings movies: {df.shape}")

        # tmdb-related columns (only once)
        df["tmdb_id"] = pd.NA
        df["tmdb_title"] = pd.NA
        df["tmdb_release_date"] = pd.NA
        df["tmdb_overview"] = pd.NA
        df["tmdb_runtime"] = pd.NA
        df["tmdb_genres"] = pd.NA
        df["tmdb_top_cast"] = pd.NA
        df["tmdb_keywords"] = pd.NA

    if limit is not None:
        df = df.head(limit).copy()
        print(f"[INFO] Limiting to first {limit} movies for test run.")

    client = TMDBClient()

    out_path_tmp = PROCESSED_DIR / "movietweetings_movies_tmdb_partial.csv"

    for idx, row in df.iterrows():
        if pd.notna(row.get("tmdb_id")):
            continue

        movie_id = row["movie_id"]
        title = row.get("title") or row.get("raw_title")
        year = row.get("year")
        year = int(year) if pd.notna(year) else None

        clean_title = normalize_title(str(title))
        print(
            f"[{idx+1}/{len(df)}] movie_id={movie_id}, "
            f"title='{clean_title}', year={year}"
        )

        # 1) search
        candidates = client.search_movie(clean_title, year=year)
        best = choose_best_tmdb_match(candidates, target_year=year)

        if best is None:
            print("  -> No TMDB match found.")
            continue

        tmdb_id = best.get("id")
        df.at[idx, "tmdb_id"] = tmdb_id
        df.at[idx, "tmdb_title"] = best.get("title")
        df.at[idx, "tmdb_release_date"] = best.get("release_date")

        # 2) details
        details = client.get_movie_details(tmdb_id)
        df.at[idx, "tmdb_overview"] = details.get("overview")
        df.at[idx, "tmdb_runtime"] = details.get("runtime")
        genres = details.get("genres", [])
        df.at[idx, "tmdb_genres"] = join_list_of_dicts(genres, key="name")

        # 3) credits
        credits = client.get_movie_credits(tmdb_id)
        cast = credits.get("cast", [])
        df.at[idx, "tmdb_top_cast"] = join_list_of_dicts(cast, key="name", top_k=5)

        # 4) keywords
        kw = client.get_movie_keywords(tmdb_id)
        keywords = kw.get("keywords", []) or kw.get("results", [])
        df.at[idx, "tmdb_keywords"] = join_list_of_dicts(keywords, key="name")

        # partial save
        if (idx + 1) % 100 == 0:
            df.to_csv(out_path_tmp, index=False)
            print(f"[INFO] Saved partial progress to {out_path_tmp}")

    out_path = (
        PROCESSED_DIR / "movietweetings_movies_tmdb_sample.csv"
        if limit
        else PROCESSED_DIR / "movietweetings_movies_tmdb.csv"
    )
    df.to_csv(out_path, index=False)
    print(f"[INFO] Saved enriched MovieTweetings movies to {out_path}")


if __name__ == "__main__":
    enrich_movietweetings_with_tmdb(limit=None)
