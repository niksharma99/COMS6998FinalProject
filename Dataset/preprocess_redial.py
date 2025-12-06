# Dataset/preprocess_redial.py

from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"


def load_split(path: Path, split_name: str) -> list[dict]:
    rows: list[dict] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            conv = json.loads(line)
            conv_id = conv.get("conversationId")
            messages = conv.get("messages", [])

            for m in messages:
                message_id = m.get("messageId")
                speaker_id = m.get("senderWorkerId")
                text = m.get("text", "")

                # flatten movie mentions
                movie_mentions = m.get("movieMentions", []) or []
                mentioned_ids = [str(mm.get("movieId")) for mm in movie_mentions if mm.get("movieId") is not None]
                mentioned_titles = [mm.get("movieName") for mm in movie_mentions if mm.get("movieName")]

                rows.append(
                    {
                        "dialog_id": conv_id,
                        "split": split_name,
                        "utterance_index": message_id,
                        "speaker_id": speaker_id,
                        "text": text,
                        "mentioned_movie_ids": "|".join(mentioned_ids) if mentioned_ids else "",
                        "mentioned_movie_titles": "|".join(mentioned_titles) if mentioned_titles else "",
                    }
                )

    return rows


def preprocess_redial():
    redial_dir = RAW_DIR / "redial"
    train_path = redial_dir / "train_data.jsonl"
    test_path = redial_dir / "test_data.jsonl"

    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(
            f"train/test jsonl not found in {redial_dir}. "
            "Expected train_data.jsonl and test_data.jsonl"
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Loading train split from {train_path}")
    train_rows = load_split(train_path, split_name="train")

    print(f"[INFO] Loading test split from {test_path}")
    test_rows = load_split(test_path, split_name="test")

    all_rows = train_rows + test_rows
    df = pd.DataFrame(all_rows)

    out_path = PROCESSED_DIR / "redial_dialogues.csv"
    df.to_csv(out_path, index=False)
    print(f"[INFO] Saved flattened ReDial dialogues to {out_path}")
    print(df.head())


if __name__ == "__main__":
    preprocess_redial()
