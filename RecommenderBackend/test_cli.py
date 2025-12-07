# from recommender import recommend

# print("=== MOVIE RECOMMENDER TEST CLI ===")
# print("Type 'exit' to quit.\n")

# while True:
#     user_input = input("User Preferences: ")
#     if user_input.lower() == "exit":
#         break

#     user_id = input("User ID (press Enter for cold start): ").strip()
#     if user_id == "":
#         user_id = None

#     print("\n--- Recommendation ---")
#     result = recommend(user_input=user_input, user_id=user_id)
#     print(result)
#     print("-----------------------\n")

import os
import logging

# --- Silence HF tokenizers fork warning ---
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# --- Reduce log noise from libraries ---
logging.getLogger("datasets").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)


import uuid
from recommender import recommend

print("=== MOVIE RECOMMENDER TEST CLI ===")
print("Type 'exit' to quit.\n")

# Only created if user presses Enter
session_user_id = None

while True:
    user_input = input("User Preference: ")
    if user_input.lower() == "exit":
        break

    raw_user_id = input("User ID (press Enter for session-based memory): ").strip()

    # ✅ Logic you asked for:
    if raw_user_id:
        # User explicitly entered an ID → use it
        user_id = raw_user_id
    else:
        # No ID provided → create or reuse session ID
        if session_user_id is None:
            session_user_id = str(uuid.uuid4())
            print(f"[Session user id created: {session_user_id}]")
        user_id = session_user_id

    print("\n--- Recommendation ---")
    result = recommend(user_input=user_input, user_id=user_id)
    print(result)
    print("-----------------------\n")
