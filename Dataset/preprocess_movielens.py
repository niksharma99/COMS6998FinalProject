# preprocess_movielens.py

from pathlib import Path
import pandas as pd
import re


def load_raw_movielens():
    base_dir = Path(__file__).resolve().parent
    raw_dir = base_dir / "raw" / "ml-1m"

    ratings_path = raw_dir / "ratings.dat"
    movies_path = raw_dir / "movies.dat"

    # MovieLens 1M: '::' special separator
    ratings = pd.read_csv(
        ratings_path,
        sep="::",
        engine="python",
        names=["userId", "movieId", "rating", "timestamp"],
    )

    movies = pd.read_csv(
        movies_path,
        sep="::",
        engine="python",
        names=["movieId", "title", "genres"],
        encoding="latin-1",
    )

    return ratings, movies


def extract_year_from_title(title: str) -> int | None:
    """
    'Toy Story (1995)' → 1995
    """
    if not isinstance(title, str):
        return None
    m = re.search(r"\((\d{4})\)", title)
    if m:
        return int(m.group(1))
    return None


def preprocess_and_save():
    base_dir = Path(__file__).resolve().parent
    processed_dir = base_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    ratings, movies = load_raw_movielens()

    print(f"[INFO] ratings: {ratings.shape}, movies: {movies.shape}")

    # ---- movies preprocessing ----
    movies["year"] = movies["title"].apply(extract_year_from_title)

    movies_out_path = processed_dir / "movielens_movies.csv"
    movies.to_csv(movies_out_path, index=False)
    print(f"[INFO] Saved movies to {movies_out_path}")

    # ---- ratings preprocessing ----
    ratings_out_path = processed_dir / "movielens_ratings.csv"
    ratings.to_csv(ratings_out_path, index=False)
    print(f"[INFO] Saved ratings to {ratings_out_path}")


if __name__ == "__main__":
    preprocess_and_save()
