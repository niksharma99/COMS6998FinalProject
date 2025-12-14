from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def call_llm(prompt: str, temperature=0.2) -> str:
    response = client.chat.completions.create(
        # model="gpt-4o-mini",
        model="ft:gpt-4o-mini-2024-07-18:org:project:movie-pref-ranker",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content.strip()


