# Dataset/tmdb_enrich_movielens.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from tmdb_client import TMDBClient


BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "processed"


def normalize_title(title: str) -> str:
    if not isinstance(title, str):
        return ""
    if "(" in title and title.strip().endswith(")"):
        idx = title.rfind("(")
        return title[:idx].strip()
    return title.strip()


def choose_best_tmdb_match(
    candidates: List[Dict[str, Any]],
    target_year: Optional[int],
) -> Optional[Dict[str, Any]]:
    if not candidates:
        return None
    if target_year is not None:
        for c in candidates:
            rd = c.get("release_date")
            if isinstance(rd, str) and len(rd) >= 4:
                y = int(rd[:4])
                if y == target_year:
                    return c
    return candidates[0]


def join_list_of_dicts(items: List[Dict[str, Any]], key: str, top_k: int | None = None) -> str:
    names = [it.get(key, "") for it in items if it.get(key)]
    if top_k is not None:
        names = names[:top_k]
    return ", ".join(names)


def enrich_movielens_with_tmdb(limit: Optional[int] = None):
    movies_path = PROCESSED_DIR / "movielens_movies.csv"
    partial_path = PROCESSED_DIR / "movielens_movies_tmdb_partial.csv"

    if partial_path.exists():
        # Resume
        print(f"[INFO] Found partial file: {partial_path}, resuming from it.")
        df = pd.read_csv(partial_path)
    else:
        if not movies_path.exists():
            raise FileNotFoundError(
                f"{movies_path} is not existed. Run preprocess_movielens.py first."
            )
        df = pd.read_csv(movies_path)
        print(f"[INFO] Loaded movies: {df.shape}")

        df["tmdb_id"] = pd.NA
        df["tmdb_title"] = pd.NA
        df["tmdb_release_date"] = pd.NA
        df["tmdb_overview"] = pd.NA
        df["tmdb_runtime"] = pd.NA
        df["tmdb_genres"] = pd.NA
        df["tmdb_top_cast"] = pd.NA
        df["tmdb_keywords"] = pd.NA

    if limit is not None:
        # Test run
        df = df.head(limit).copy()
        print(f"[INFO] Limiting to first {limit} movies for test run.")

    client = TMDBClient()
    out_path_tmp = PROCESSED_DIR / "movielens_movies_tmdb_partial.csv"

    for idx, row in df.iterrows():
        # 1. Resume: skip already processed
        if pd.notna(row.get("tmdb_id")):
            continue

        ml_movie_id = row["movieId"]
        title = row["title"]
        year = row.get("year")
        year = int(year) if pd.notna(year) else None

        clean_title = normalize_title(title)
        print(f"[{idx+1}/{len(df)}] movieId={ml_movie_id}, title='{clean_title}', year={year}")

        # 2. Search TMDB
        candidates = client.search_movie(clean_title, year=year)
        best = choose_best_tmdb_match(candidates, target_year=year)

        if best is None:
            print("  -> No TMDB match found.")
            continue

        tmdb_id = best.get("id")
        df.at[idx, "tmdb_id"] = tmdb_id
        df.at[idx, "tmdb_title"] = best.get("title")
        df.at[idx, "tmdb_release_date"] = best.get("release_date")

        # 3. Get details
        details = client.get_movie_details(tmdb_id)
        df.at[idx, "tmdb_overview"] = details.get("overview")
        df.at[idx, "tmdb_runtime"] = details.get("runtime")
        genres = details.get("genres", [])
        df.at[idx, "tmdb_genres"] = join_list_of_dicts(genres, key="name")

        # 4. Get credits
        credits = client.get_movie_credits(tmdb_id)
        cast = credits.get("cast", [])
        df.at[idx, "tmdb_top_cast"] = join_list_of_dicts(cast, key="name", top_k=5)

        # 5. Get keywords
        kw = client.get_movie_keywords(tmdb_id)
        keywords = kw.get("keywords", []) or kw.get("results", [])
        df.at[idx, "tmdb_keywords"] = join_list_of_dicts(keywords, key="name")

        # 6. Save partial every 200
        if (idx + 1) % 200 == 0:
            df.to_csv(out_path_tmp, index=False)
            print(f"[INFO] Saved partial progress to {out_path_tmp}")

    out_path = (
        PROCESSED_DIR / "movielens_movies_tmdb_sample.csv"
        if limit
        else PROCESSED_DIR / "movielens_movies_tmdb.csv"
    )
    df.to_csv(out_path, index=False)
    print(f"[INFO] Saved enriched movies to {out_path}")


if __name__ == "__main__":
    enrich_movielens_with_tmdb(limit=None)
