# Dataset/download_redial.py

from __future__ import annotations
from pathlib import Path
import zipfile
import io
import requests

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"

REDIAL_URL = "https://github.com/ReDialData/website/raw/data/redial_dataset.zip"

def download_redial():
    out_dir = RAW_DIR / "redial"
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_path = out_dir / "redial_dataset.zip"
    if zip_path.exists():
        print(f"[INFO] {zip_path} already exists, skip download.")
    else:
        print(f"[INFO] Downloading ReDial from {REDIAL_URL}")
        resp = requests.get(REDIAL_URL)
        resp.raise_for_status()
        zip_path.write_bytes(resp.content)
        print(f"[INFO] Saved zip to {zip_path}")

    # unzip
    print("[INFO] Extracting zip...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)
    print(f"[INFO] Extracted to {out_dir}")
    print("[INFO] Please check what JSONL file name you got (e.g. redial_dataset.jsonl) and update preprocess_redial.py if needed.")

if __name__ == "__main__":
    download_redial()
