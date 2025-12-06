# Dataset/preprocess_inspired.py

from __future__ import annotations
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw" / "inspired"
PROCESSED_DIR = BASE_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_split(split_name: str) -> pd.DataFrame:
    path = RAW_DIR / f"{split_name}.tsv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run download_inspired.py first.")
    print(f"[INFO] Loading {path}")
    df = pd.read_csv(path, sep="\t")
    df["split"] = split_name  # train/dev/test
    return df


def preprocess_dialogs():
    dfs = []
    for split in ["train", "dev", "test"]:
        dfs.append(load_split(split))

    all_df = pd.concat(dfs, ignore_index=True)
    out_path = PROCESSED_DIR / "inspired_dialogs.csv"
    all_df.to_csv(out_path, index=False)
    print(f"[INFO] Saved combined dialogs to {out_path} with shape {all_df.shape}")


def preprocess_movie_db():
    movie_db_path = RAW_DIR / "movie_database.tsv"
    if not movie_db_path.exists():
        raise FileNotFoundError("movie_database.tsv not found. Run download_inspired.py first.")

    print(f"[INFO] Loading {movie_db_path}")
    mdf = pd.read_csv(movie_db_path, sep="\t")

    out_path = PROCESSED_DIR / "inspired_movie_database.csv"
    mdf.to_csv(out_path, index=False)
    print(f"[INFO] Saved movie database to {out_path} with shape {mdf.shape}")


def main():
    preprocess_dialogs()
    preprocess_movie_db()


if __name__ == "__main__":
    main()
