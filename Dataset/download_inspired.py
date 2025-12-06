# Dataset/download_inspired.py

from __future__ import annotations
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
INSPIRED_DIR = RAW_DIR / "inspired"

INSPIRED_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://raw.githubusercontent.com/sweetpeach/Inspired/master/data"  # :contentReference[oaicite:0]{index=0}

DIALOG_FILES = {
    "train.tsv": f"{BASE_URL}/dialog_data/train.tsv",
    "dev.tsv": f"{BASE_URL}/dialog_data/dev.tsv",
    "test.tsv": f"{BASE_URL}/dialog_data/test.tsv",
}

MOVIE_DB_FILE = {
    "movie_database.tsv": f"{BASE_URL}/movie_database.tsv",
}


def download_file(url: str, out_path: Path):
    print(f"[INFO] Downloading {url} -> {out_path}")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    print(f"[INFO] Saved {out_path} ({len(resp.content):,} bytes)")


def main():
    # dialog splits
    for fname, url in DIALOG_FILES.items():
        out_path = INSPIRED_DIR / fname
        if out_path.exists():
            print(f"[SKIP] {out_path} already exists")
            continue
        download_file(url, out_path)

    # movie database
    for fname, url in MOVIE_DB_FILE.items():
        out_path = INSPIRED_DIR / fname
        if out_path.exists():
            print(f"[SKIP] {out_path} already exists")
            continue
        download_file(url, out_path)

    print("[DONE] INSPIRED dataset downloaded under raw/inspired/")


if __name__ == "__main__":
    main()
