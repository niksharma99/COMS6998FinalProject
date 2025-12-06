# Dataset/preprocess_movietweetings.py

from __future__ import annotations
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw" / "movietweetings"
PROCESSED_DIR = BASE_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def preprocess_ratings():
    path = RAW_DIR / "ratings.dat"
    if not path.exists():
        raise FileNotFoundError("ratings.dat not found. Run download_movietweetings.py first.")

    print(f"[INFO] Loading {path}")
    df = pd.read_csv(
        path,
        sep="::",
        engine="python",
        header=None,
        names=["user_id", "movie_id", "rating", "timestamp"],
    )

    out_path = PROCESSED_DIR / "movietweetings_ratings.csv"
    df.to_csv(out_path, index=False)
    print(f"[INFO] Saved ratings to {out_path} with shape {df.shape}")


def split_title_year(raw_title: str):
    """Parse 'Pulp Fiction (1994)' -> ('Pulp Fiction', 1994)."""
    if not isinstance(raw_title, str):
        return "", None
    raw_title = raw_title.strip()
    if raw_title.endswith(")") and "(" in raw_title:
        idx = raw_title.rfind("(")
        title = raw_title[:idx].strip()
        year_str = raw_title[idx + 1 : -1]
        try:
            year = int(year_str)
        except ValueError:
            year = None
        return title, year
    return raw_title, None


def preprocess_movies():
    path = RAW_DIR / "movies.dat"
    if not path.exists():
        raise FileNotFoundError("movies.dat not found. Run download_movietweetings.py first.")

    print(f"[INFO] Loading {path}")
    df = pd.read_csv(
        path,
        sep="::",
        engine="python",
        header=None,
        names=["movie_id", "raw_title", "genres"],
    )

    titles, years = [], []
    for t in df["raw_title"]:
        title, year = split_title_year(t)
        titles.append(title)
        years.append(year)

    df["title"] = titles
    df["year"] = years

    # genres: "Crime|Thriller" -> list or keep as string; 여기서는 string 유지
    out_path = PROCESSED_DIR / "movietweetings_movies.csv"
    df.to_csv(out_path, index=False)
    print(f"[INFO] Saved movies to {out_path} with shape {df.shape}")


def preprocess_users():
    path = RAW_DIR / "users.dat"
    if not path.exists():
        raise FileNotFoundError("users.dat not found. Run download_movietweetings.py first.")

    print(f"[INFO] Loading {path}")
    df = pd.read_csv(
        path,
        sep="::",
        engine="python",
        header=None,
        names=["user_id", "twitter_id"],
    )

    out_path = PROCESSED_DIR / "movietweetings_users.csv"
    df.to_csv(out_path, index=False)
    print(f"[INFO] Saved users to {out_path} with shape {df.shape}")


def main():
    preprocess_ratings()
    preprocess_movies()
    preprocess_users()


if __name__ == "__main__":
    main()
