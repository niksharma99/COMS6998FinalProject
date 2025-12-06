# Dataset/download_ccpe.py

from __future__ import annotations
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"

CCPE_URL = "https://raw.githubusercontent.com/google-research-datasets/ccpe/main/data.json"

def download_ccpe():
    out_dir = RAW_DIR / "ccpe"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ccpe_data.json"

    if out_path.exists():
        print(f"[INFO] {out_path} already exists, skip download.")
        return

    print(f"[INFO] Downloading CCPE from {CCPE_URL}")
    resp = requests.get(CCPE_URL)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    print(f"[INFO] Saved CCPE data to {out_path}")

if __name__ == "__main__":
    download_ccpe()
