#!/usr/bin/env python3
# RecommenderBackend/eval_qualitative_gpt.py

"""
Qualitative evaluation: GPT-as-judge.

We simulate short 2-turn conversations from rec_log.jsonl:

  USER: <msg 1>
  ASSISTANT: <top-K movie titles for msg 1>
  USER: <msg 2>
  ASSISTANT: <top-K titles for msg 2>

We then ask GPT to rate:
  - relevance
  - diversity
  - personalization
  - explanation_quality
  - overall_satisfaction

on a 1-5 scale, and compute average scores across all conversations.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from openai import OpenAI

from config import MOVIE_EMBED_PATH, FINAL_K
from embedding_loader import load_movie_embeddings

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "rec_log.jsonl"

client = OpenAI()

EVAL_SYSTEM_PROMPT = "You are a strict but fair evaluator of movie recommendation quality."

EVAL_TEMPLATE = """You are evaluating a movie recommendation assistant.

You will be given a short conversation between a USER and ASSISTANT.
The pattern is:
- USER expresses their tastes or constraints
- ASSISTANT provides a set of movie recommendations
- USER refines their preferences
- ASSISTANT updates the recommendations.

Your task:
1. Read the entire conversation.
2. Rate the assistant's performance on:
   - relevance: how well do the recommendations match the user's tastes?
   - diversity: how diverse are the recommendations while still matching preferences?
   - personalization: how well does the assistant adapt to new user feedback across turns?
   - explanation_quality: how clear and convincing are the explanations for each recommendation?
   - overall_satisfaction: your overall impression of the system.

Each rating must be an INTEGER from 1 to 5.

3. Provide a 1–3 sentence justification.

Return a single JSON object with keys:
"relevance", "diversity", "personalization", "explanation_quality", "overall_satisfaction", "comment".

Conversation:
---
{conversation_text}
---
"""


def load_logs() -> List[dict]:
    if not LOG_PATH.exists():
        print(f"No log file found at {LOG_PATH}.")
        return []
    rows = []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def build_conversations(
    logs: List[dict],
    movie_metadata: List[dict],
    min_turns: int = 2,
) -> List[str]:
    """
    For each user_id with >= min_turns, build a small 2-turn conversation:
      USER: msg1
      ASSISTANT: top-K titles from rec1
      USER: msg2
      ASSISTANT: top-K titles from rec2
    """
    by_user: Dict[str, List[dict]] = defaultdict(list)
    for rec in logs:
        uid = rec.get("user_id")
        if not uid:
            continue
        by_user[uid].append(rec)

    conversations = []

    for uid, recs in by_user.items():
        # Must have msg_index to order turns
        recs = [r for r in recs if "msg_index" in r]
        if len(recs) < min_turns:
            continue

        recs.sort(key=lambda r: int(r["msg_index"]))

        first, second = recs[0], recs[1]

        def titles_from_rec(r: dict) -> List[str]:
            cand_idx = [int(i) for i in r.get("candidate_indices", [])][:FINAL_K]
            titles = []
            for idx in cand_idx:
                if 0 <= idx < len(movie_metadata):
                    meta = movie_metadata[idx]
                    title = meta.get("title") or meta.get("movie_title") or "Unknown Title"
                    titles.append(title)
            return titles

        titles1 = titles_from_rec(first)
        titles2 = titles_from_rec(second)

        lines: List[str] = []
        lines.append(f"USER: {first.get('user_input', '').strip()}")
        lines.append("ASSISTANT: Here are some movies you might like:")
        for t in titles1:
            lines.append(f"- {t}")

        lines.append("")
        lines.append(f"USER: {second.get('user_input', '').strip()}")
        lines.append("ASSISTANT: Updating your recommendations:")
        for t in titles2:
            lines.append(f"- {t}")

        conversation_text = "\n".join(lines)
        conversations.append(conversation_text)

    return conversations


def evaluate_conversation(conv_text: str) -> dict:
    prompt = EVAL_TEMPLATE.format(conversation_text=conv_text)

    resp = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {"role": "system", "content": EVAL_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    content = resp.choices[0].message.content
    try:
        scores = json.loads(content)
    except json.JSONDecodeError:
        # In practice you'd parse out the JSON subset; for presentation, we assume it's valid.
        scores = {}
    return scores


def main():
    movie_embeddings, movie_metadata = load_movie_embeddings(MOVIE_EMBED_PATH)
    logs = load_logs()
    conversations = build_conversations(logs, movie_metadata)

    print(f"Built {len(conversations)} 2-turn conversations from logs.")

    all_scores = []

    for i, conv in enumerate(conversations):
        print(f"Evaluating conversation {i+1}/{len(conversations)}...")
        scores = evaluate_conversation(conv)
        if scores:
            all_scores.append(scores)

    if not all_scores:
        print("No scores collected.")
        return

    df = pd.DataFrame(all_scores)

    numeric_cols = [
        "relevance",
        "diversity",
        "personalization",
        "explanation_quality",
        "overall_satisfaction",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    summary = df[numeric_cols].mean().to_frame(name="mean_score").round(2)
    print("\nGPT-as-judge qualitative results (1–5):")
    print(summary.to_string())


if __name__ == "__main__":
    main()
