from llm import call_llm

def extract_structured_taste(user_text: str) -> str:
    prompt = f"""
Convert this user message into a clean movie taste profile for embedding.

User:
{user_text}

Return a single paragraph describing:
- preferred genres
- tone/mood
- pacing
- themes
- examples if any

Do NOT include filler or explanation.
"""

    return call_llm(prompt, temperature=0.1)
