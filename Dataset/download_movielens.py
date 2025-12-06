# download_movielens.py

from pathlib import Path
import requests
import zipfile

MOVIELENS_1M_URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"


def download_movielens_1m():
    base_dir = Path(__file__).resolve().parent
    raw_dir = base_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    zip_path = raw_dir / "ml-1m.zip"

    if zip_path.exists():
        print(f"[INFO] {zip_path} already exists, skip downloading.")
        return zip_path

    print(f"[INFO] Downloading MovieLens 1M from {MOVIELENS_1M_URL}...")
    resp = requests.get(MOVIELENS_1M_URL, stream=True)
    resp.raise_for_status()

    with zip_path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"[INFO] Downloaded to {zip_path}")
    return zip_path


def extract_movielens_1m(zip_path: Path):
    base_dir = Path(__file__).resolve().parent
    raw_dir = base_dir / "raw"
    extract_dir = raw_dir / "ml-1m"

    if extract_dir.exists():
        print(f"[INFO] {extract_dir} already exists, skip extracting.")
        return extract_dir

    print(f"[INFO] Extracting {zip_path} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(raw_dir)

    print(f"[INFO] Extracted to {extract_dir}")
    return extract_dir


if __name__ == "__main__":
    zip_path = download_movielens_1m()
    extract_movielens_1m(zip_path)
