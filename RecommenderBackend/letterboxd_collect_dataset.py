#!/usr/bin/env python3
"""
letterboxd_collect_dataset.py

Educational example: collect a small Letterboxd-like user–movie dataset
using the official Letterboxd API.

Pipeline:
  1. Start from a "top" user (e.g. 'davidsims').
  2. Use the API to:
       - resolve username -> member LID
       - pull recent log entries for that member + their friends
  3. For each member (seed + friends):
       - identify their "top 4" favorite films as highest-rated entries
       - collect a chunk of their rating history + reviews
  4. Save to letterboxd_dataset.jsonl for downstream fine-tuning / embeddings.

NOTE:
  - You need LETTERBOXD_CLIENT_ID and LETTERBOXD_CLIENT_SECRET in your environment.
  - This script only uses *public* API endpoints and respects the service's rate limits.
  - In your talk, you can honestly say you used the official API rather than scraping HTML.
"""

import os
import sys
import time
import json
import argparse
from typing import Dict, List, Any, Tuple

import requests

# --- Config -----------------------------------------------------------------

API_BASE = "https://api.letterboxd.com/api/v0"

CLIENT_ID = os.getenv("LETTERBOXD_CLIENT_ID")
CLIENT_SECRET = os.getenv("LETTERBOXD_CLIENT_SECRET")

# Be nice to the API; small sleep between calls
API_SLEEP_SEC = 0.25


# --- Low-level helpers ------------------------------------------------------

def get_access_token() -> str:
    """
    OAuth2 Client Credentials flow.
    See Letterboxd docs: POST /auth/token with grant_type=client_credentials. :contentReference[oaicite:4]{index=4}
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError(
            "LETTERBOXD_CLIENT_ID and LETTERBOXD_CLIENT_SECRET must be set in your environment."
        )

    resp = requests.post(
        f"{API_BASE}/auth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["access_token"]


def api_get(path: str, token: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Helper for GET calls to the Letterboxd API."""
    url = f"{API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    resp = requests.get(url, headers=headers, params=params or {}, timeout=10)
    resp.raise_for_status()
    time.sleep(API_SLEEP_SEC)
    return resp.json()


def get_member_lid_from_username(username: str) -> str:
    """
    Resolve a Letterboxd username to a member LID using a HEAD request.

    Per the docs, the LID is exposed as the `x-letterboxd-identifier` header
    when you hit the profile URL. :contentReference[oaicite:5]{index=5}
    """
    url = f"https://letterboxd.com/{username}/"
    resp = requests.head(url, timeout=10)
    resp.raise_for_status()
    lid = resp.headers.get("x-letterboxd-identifier")
    if not lid:
        raise RuntimeError(f"No x-letterboxd-identifier header for user {username!r}")
    return lid


def get_member_profile(member_lid: str, token: str) -> Dict[str, Any]:
    """GET /member/{id} → Member details (username, displayName, etc.). :contentReference[oaicite:6]{index=6}"""
    return api_get(f"/member/{member_lid}", token=token)


# --- Friend graph via log entries ------------------------------------------

def get_friend_members(
    seed_member_lid: str,
    token: str,
    max_friends: int = 50,
) -> Dict[str, str]:
    """
    Approximate a 'friends' set by asking for log entries associated with
    the seed's friends.

    We use GET /log-entries with:
      - member = seed_member_lid
      - includeFriends = 'Only'
      - filter = 'NoDuplicateMembers'
    This returns log entries created by the seed's friends, with each entry
    listing its 'owner' MemberSummary. :contentReference[oaicite:7]{index=7}
    """
    params = {
        "member": seed_member_lid,
        "includeFriends": "Only",
        "filter": "NoDuplicateMembers",
        "perPage": max_friends,
        "sort": "WhenAdded",
    }

    data = api_get("/log-entries", token=token, params=params)
    items = data.get("items", [])
    friends: Dict[str, str] = {}

    for item in items:
        owner = item.get("owner") or {}
        lid = owner.get("id")
        username = owner.get("username")
        if lid and lid not in friends:
            friends[lid] = username or f"member_{lid}"

    return friends


# --- Log entries (ratings, diary, reviews) ---------------------------------

def get_member_log_entries(
    member_lid: str,
    token: str,
    per_page: int = 200,
) -> List[Dict[str, Any]]:
    """
    Get recent rated log entries for a specific member using GET /log-entries.
    We filter to entries that have a rating (where=Rated) and belong to that member
    (memberRelationship=Owner). :contentReference[oaicite:8]{index=8}
    """
    params = {
        "member": member_lid,
        "memberRelationship": "Owner",
        "where": ["Rated"],
        "perPage": min(per_page, 100),  # API max is 100 per page
        "sort": "WhenAdded",            # or "Date" for diaryDate sort
    }

    all_items: List[Dict[str, Any]] = []
    cursor = None

    while True:
        if cursor:
            params["cursor"] = cursor
        data = api_get("/log-entries", token=token, params=params)
        items = data.get("items", [])
        all_items.extend(items)

        cursor = data.get("next")
        if not cursor or len(all_items) >= per_page:
            break

    return all_items[:per_page]


def extract_top_4_favorites(log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Approximate 'favorite films' as the top 4 highest-rated log entries.

    For presentation you can say:
      “We treated each user’s top 4 highest-rated films as their favorites.”
    """
    # Filter entries that actually have a rating
    rated = [
        e for e in log_entries
        if isinstance(e.get("rating"), (float, int))
    ]
    # Sort by rating desc, then by newest first (if we have any ordering key)
    rated.sort(key=lambda e: (e.get("rating", 0.0)), reverse=True)
    return rated[:4]


def simplify_log_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Turn a raw LogEntry object into a compact dict with only the fields we care about
    for downstream modeling.
    """
    film = entry.get("film") or {}
    diary_details = entry.get("diaryDetails") or {}
    review_details = entry.get("review") or {}

    # LogEntry.film is a FilmSummary: id, name, releaseYear, etc. :contentReference[oaicite:9]{index=9}
    film_id = film.get("id")
    film_title = film.get("name")
    film_year = film.get("releaseYear")

    rating = entry.get("rating")  # 0.5–5.0 in 0.5 increments :contentReference[oaicite:10]{index=10}
    diary_date = diary_details.get("diaryDate")  # YYYY-MM-DD if present
    review_text = review_details.get("text")  # LBML string if present :contentReference[oaicite:11]{index=11}

    return {
        "film_id": film_id,
        "film_title": film_title,
        "film_year": film_year,
        "rating": rating,
        "diary_date": diary_date,
        "review_text": review_text,
    }


# --- Main collection routine -----------------------------------------------

def collect_dataset(
    seed_username: str,
    max_friends: int,
    per_user_entries: int,
    output_path: str,
) -> None:
    """
    High-level orchestration:

      - Resolve seed username -> member LID
      - Get a small set of that member's 'friends'
      - For each member (seed + friends), fetch rated log entries
      - Derive 'favorites' and history
      - Save one JSON object per user to `output_path`
    """
    token = get_access_token()
    print(f"[auth] Obtained access token")

    seed_lid = get_member_lid_from_username(seed_username)
    print(f"[seed] Username '{seed_username}' -> member LID '{seed_lid}'")

    # Also fetch profile so we have canonical username/displayName
    seed_profile = get_member_profile(seed_lid, token)
    seed_username_api = seed_profile.get("username", seed_username)

    # Discover friends via /log-entries with includeFriends=Only
    friends = get_friend_members(seed_lid, token=token, max_friends=max_friends)
    print(f"[friends] Found {len(friends)} friend(s) of {seed_username_api}")

    # Build list of member LIDs to process: seed + friends
    members_to_process: List[Tuple[str, str]] = [(seed_lid, seed_username_api)]
    for lid, uname in friends.items():
        members_to_process.append((lid, uname))

    print(f"[collect] Will process up to {len(members_to_process)} members")

    with open(output_path, "w", encoding="utf-8") as f_out:
        for idx, (member_lid, username) in enumerate(members_to_process, start=1):
            print(f"[member {idx}/{len(members_to_process)}] {username} ({member_lid})")

            try:
                log_entries = get_member_log_entries(
                    member_lid, token=token, per_page=per_user_entries
                )
            except Exception as e:
                print(f"  ! Failed to fetch log entries for {username}: {e}")
                continue

            if not log_entries:
                print("  (no rated entries)")
                continue

            # Simplify entries
            simplified_entries = [simplify_log_entry(e) for e in log_entries]
            top4_entries = extract_top_4_favorites(log_entries)
            simplified_top4 = [simplify_log_entry(e) for e in top4_entries]

            # Build a compact user record for downstream modeling.
            user_record = {
                "member_lid": member_lid,
                "username": username,
                "n_entries": len(simplified_entries),
                "favorites_top4": simplified_top4,
                "rating_history": simplified_entries,
            }

            f_out.write(json.dumps(user_record) + "\n")

    print(f"[done] Wrote dataset to {output_path}")


# --- CLI --------------------------------------------------------------------

def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Collect a small Letterboxd-style dataset for recommender fine-tuning."
    )
    p.add_argument(
        "--seed-username",
        type=str,
        default="davidsims",
        help="Seed Letterboxd username (e.g. 'davidsims').",
    )
    p.add_argument(
        "--max-friends",
        type=int,
        default=20,
        help="Maximum number of friends to include from the seed user's graph.",
    )
    p.add_argument(
        "--per-user-entries",
        type=int,
        default=200,
        help="Max number of rated log entries to fetch per member.",
    )
    p.add_argument(
        "--output",
        type=str,
        default="letterboxd_dataset.jsonl",
        help="Path to output JSONL file.",
    )
    return p.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()

    try:
        collect_dataset(
            seed_username=args.seed_username,
            max_friends=args.max_friends,
            per_user_entries=args.per_user_entries,
            output_path=args.output,
        )
    except Exception as exc:
        print(f"[error] {exc}")
        sys.exit(1)
