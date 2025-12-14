# qualitative_eval.py
import json
from openai import OpenAI

client = OpenAI()

EVAL_SYSTEM_PROMPT = "You are a strict but fair evaluator of movie recommendation quality."

EVAL_TEMPLATE = """You are evaluating a movie recommendation assistant.

You will be given a short conversation between a USER and ASSISTANT.
The pattern is: user message -> assistant recommendations -> user refinement -> assistant recommendations.

Your task:
1. Read the entire conversation.
2. Rate the assistant's performance on:
   - relevance
   - diversity
   - personalization
   - explanation_quality
   - overall_satisfaction
Each from 1 to 5 (integers).

3. Provide a 1-3 sentence justification.

Return a single JSON object with keys:
"relevance", "diversity", "personalization", "explanation_quality", "overall_satisfaction", "comment".

Conversation:
---
{conversation_text}
---
"""

def evaluate_conversation(conversation_text: str) -> dict:
    prompt = EVAL_TEMPLATE.format(conversation_text=conversation_text)

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
        # if the model adds extra text, you can regex out the JSON in practice
        scores = {}
    return scores
