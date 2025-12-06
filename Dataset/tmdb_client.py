# Dataset/tmdb_client.py

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# .env
load_dotenv()


class TMDBClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        language: str = "en-US",
        rate_limit_sleep: float = 0.20,
    ) -> None:
        if api_key is None:
            api_key = os.getenv("TMDB_API_KEY")

        if not api_key:
            raise ValueError(
                "TMDB_API_KEY not found. Set TMDB_API_KEY in .env file or pass api_key parameter."
            )

        self.api_key = api_key
        self.language = language
        self.rate_limit_sleep = rate_limit_sleep
        self.base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        merged = {"api_key": self.api_key, "language": self.language}
        merged.update(params)

        resp = requests.get(url, params=merged, timeout=10)
        time.sleep(self.rate_limit_sleep)

        if resp.status_code != 200:
            print(f"[TMDB] GET {url} failed: {resp.status_code} {resp.text[:200]}")
            return {}
        return resp.json()

    def search_movie(self, title: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"query": title}
        if year is not None:
            params["year"] = year
        data = self._get("/search/movie", params=params)
        return data.get("results", []) if isinstance(data, dict) else []

    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}", params={})

    def get_movie_credits(self, movie_id: int) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}/credits", params={})

    def get_movie_keywords(self, movie_id: int) -> Dict[str, Any]:
        return self._get(f"/movie/{movie_id}/keywords", params={})
