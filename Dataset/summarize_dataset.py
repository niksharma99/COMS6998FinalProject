# Dataset/summarize_dataset.py

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "processed"


DATASETS: List[Dict[str, str]] = [
    # Movie / item-level tables
    {
        "name": "MovieLens Movies (TMDB enriched)",
        "filename": "movielens_movies_tmdb.csv",
        "category": "movie",
    },
    {
        "name": "MovieTweetings Movies (TMDB enriched)",
        "filename": "movietweetings_movies_tmdb.csv",
        "category": "movie",
    },
    {
        "name": "INSPIRED Movie Database (TMDB enriched)",
        "filename": "inspired_movie_database_tmdb.csv",
        "category": "movie",
    },

    # Ratings / interactions
    {
        "name": "MovieLens Ratings",
        "filename": "movielens_ratings.csv",
        "category": "rating",
    },
    {
        "name": "MovieTweetings Ratings",
        "filename": "movietweetings_ratings.csv",
        "category": "rating",
    },

    # Dialogue / text corpora
    {
        "name": "ReDial Dialogues",
        "filename": "redial_dialogues.csv",
        "category": "dialogue",
    },
    {
        "name": "CCPE Dialogues",
        "filename": "ccpe_dialogues.csv",
        "category": "dialogue",
    },
    {
        "name": "GoEmotions Texts",
        "filename": "goemotions_text_emotions.csv",  # or goemotions_text_emotions.csv, depending on your script
        "category": "text",
    },
]


def count_rows(path: Path) -> Optional[int]:
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        return len(df)
    except Exception as e:
        print(f"[WARN] Failed to read {path}: {e}")
        return None


def main():
    print(f"[INFO] Scanning processed datasets in: {PROCESSED_DIR}\n")

    results = []
    total_all = 0
    totals_by_category = {}

    for spec in DATASETS:
        name = spec["name"]
        filename = spec["filename"]
        category = spec["category"]

        path = PROCESSED_DIR / filename
        n_rows = count_rows(path)

        if n_rows is None:
            row_str = "NOT FOUND"
        else:
            row_str = f"{n_rows:,}"
            total_all += n_rows
            totals_by_category[category] = totals_by_category.get(category, 0) + n_rows

        results.append((name, filename, category, n_rows, row_str))

    # --- Plain text summary ---
    print("=== Dataset Summary (Plain Text) ===")
    for name, filename, category, n_rows, row_str in results:
        print(f"- {name:40s} [{category}]  -> {row_str} rows  ({filename})")

    print("\n=== Totals by Category ===")
    for cat, val in totals_by_category.items():
        print(f"- {cat:8s}: {val:,}")

    print(f"\n[INFO] Total rows across all available datasets: {total_all:,}\n")

    # --- Markdown table for README ---
    print("=== Markdown Table (copy-paste into README) ===\n")
    print("| Dataset | Category | Count | File |")
    print("|--------|----------|-------|------|")
    for name, filename, category, n_rows, row_str in results:
        print(f"| {name} | {category} | {row_str} | `{filename}` |")

    print(
        f"\n> **Total rows across all processed datasets:** "
        f"`{total_all:,}` (only counting files that exist and loaded successfully)."
    )


if __name__ == "__main__":
    main()
