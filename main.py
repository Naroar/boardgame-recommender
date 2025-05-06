from fastapi import FastAPI, Query
from typing import List, Optional
from recommender import get_recommendations

app = FastAPI()

@app.get("/recommend")
def recommend(
    players: int,
    complexity: Optional[List[str]] = Query(default=None),
    themes: Optional[List[str]] = Query(default=None)
):
    return get_recommendations(players, complexity, themes)
