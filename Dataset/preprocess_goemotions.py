# Dataset/preprocess_goemotions.py

from __future__ import annotations
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"

FILES = ["goemotions_1.csv", "goemotions_2.csv", "goemotions_3.csv"]

def preprocess_goemotions():
    src_dir = RAW_DIR / "goemotions"
    dfs = []
    for fname in FILES:
        path = src_dir / fname
        if not path.exists():
            raise FileNotFoundError(f"{path} missing. Run download_goemotions.py.")
        df = pd.read_csv(path)
        dfs.append(df)

    full = pd.concat(dfs, ignore_index=True)

    meta_cols = {"text", "id", "author", "subreddit", "link_id", "parent_id", "created_utc",
                 "rater_id", "example_very_unclear"}
    emotion_cols = [c for c in full.columns if c not in meta_cols]

    def row_to_emotions(row):
        labels = [emo for emo in emotion_cols if row[emo] == 1]
        return ",".join(labels)

    full["emotions"] = full.apply(row_to_emotions, axis=1)

    out = full[["id", "text", "emotions"]]
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "goemotions_text_emotions.csv"
    out.to_csv(out_path, index=False)
    print(f"[INFO] Saved GoEmotions processed file to {out_path}")
    print(out.head())

if __name__ == "__main__":
    preprocess_goemotions()
