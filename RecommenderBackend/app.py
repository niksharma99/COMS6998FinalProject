from fastapi import FastAPI
from pydantic import BaseModel
from recommender import recommend

app = FastAPI()

from typing import Optional

class TasteRequest(BaseModel):
    user_input: str
    user_id: Optional[str] = None


@app.post("/recommend")
def recommend_api(req: TasteRequest):
    return {
        "recommendation": recommend(
            user_input=req.user_input,
            user_id=req.user_id
        )
    }

@app.get("/")
def root():
    return {"status": "Movie recommender is running."}
