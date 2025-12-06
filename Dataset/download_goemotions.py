# Dataset/download_goemotions.py

from __future__ import annotations
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"

URL_ROOT = "https://storage.googleapis.com/gresearch/goemotions/data/full_dataset"
FILES = ["goemotions_1.csv", "goemotions_2.csv", "goemotions_3.csv"]

def download_goemotions():
    out_dir = RAW_DIR / "goemotions"
    out_dir.mkdir(parents=True, exist_ok=True)

    for fname in FILES:
        url = f"{URL_ROOT}/{fname}"
        out_path = out_dir / fname
        if out_path.exists():
            print(f"[INFO] {out_path} already exists, skip.")
            continue
        print(f"[INFO] Downloading {url}")
        resp = requests.get(url)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)
        print(f"[INFO] Saved to {out_path}")

if __name__ == "__main__":
    download_goemotions()
