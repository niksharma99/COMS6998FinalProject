# Dataset/preprocess_ccpe.py

from __future__ import annotations
from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"

def preprocess_ccpe():
    src_path = RAW_DIR / "ccpe" / "ccpe_data.json"
    if not src_path.exists():
        raise FileNotFoundError(f"{src_path} not found. Run download_ccpe.py first.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with src_path.open("r", encoding="utf-8") as f:
        conversations = json.load(f)

    rows = []
    for conv in conversations:
        conv_id = conv.get("conversationId")
        for utt in conv.get("utterances", []):
            rows.append(
                {
                    "dialog_id": conv_id,
                    "utterance_index": utt.get("index"),
                    "speaker": utt.get("speaker"),  # "USER" or "ASSISTANT"
                    "text": utt.get("text", ""),
                }
            )

    df = pd.DataFrame(rows)
    out_path = PROCESSED_DIR / "ccpe_dialogues.csv"
    df.to_csv(out_path, index=False)
    print(f"[INFO] Saved flattened CCPE dialogues to {out_path}")
    print(df.head())

if __name__ == "__main__":
    preprocess_ccpe()
