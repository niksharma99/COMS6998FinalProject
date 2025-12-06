# Dataset/download_movietweetings.py

from __future__ import annotations
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
MT_DIR = RAW_DIR / "movietweetings"

MT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://raw.githubusercontent.com/sidooms/MovieTweetings/master/latest"  # :contentReference[oaicite:3]{index=3}

FILES = {
    "ratings.dat": f"{BASE_URL}/ratings.dat",
    "movies.dat": f"{BASE_URL}/movies.dat",
    "users.dat": f"{BASE_URL}/users.dat",
}


def download_file(url: str, out_path: Path):
    print(f"[INFO] Downloading {url} -> {out_path}")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    print(f"[INFO] Saved {out_path} ({len(resp.content):,} bytes)")


def main():
    for fname, url in FILES.items():
        out_path = MT_DIR / fname
        if out_path.exists():
            print(f"[SKIP] {out_path} already exists")
            continue
        download_file(url, out_path)

    print("[DONE] MovieTweetings latest snapshot downloaded under raw/movietweetings/")


if __name__ == "__main__":
    main()
