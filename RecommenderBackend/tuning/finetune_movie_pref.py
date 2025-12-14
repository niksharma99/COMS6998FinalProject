# RecommenderBackend/finetune_movie_pref.py

"""
Launch a GPT fine-tuning job for the movie preference predictor.

Assumes movie_pref_train.jsonl and movie_pref_val.jsonl were
created by build_finetune_data.py and live under artifacts/.
"""

from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"

TRAIN_FILE = ARTIFACTS / "movie_pref_train.jsonl"
VAL_FILE = ARTIFACTS / "movie_pref_val.jsonl"

client = OpenAI()  # reads OPENAI_API_KEY from env


def main():
    # 1. Upload training file
    train = client.files.create(
        file=open(TRAIN_FILE, "rb"),
        purpose="fine-tune",
    )

    # 2. Upload validation file
    val = client.files.create(
        file=open(VAL_FILE, "rb"),
        purpose="fine-tune",
    )

    # 3. Create the fine-tuning job
    job = client.fine_tuning.jobs.create(
        training_file=train.id,
        validation_file=val.id,
        model="gpt-4o-mini-2024-07-18",
        suffix="movie-pref-ranker",
    )

    print("Fine-tune job created.")
    print("Job ID:", job.id)
    print(job)


if __name__ == "__main__":
    main()
