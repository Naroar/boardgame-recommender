# --- Enhancements to recommender.py ---

import json, os, time, hashlib, requests, xmltodict
from typing import List, Optional
from fastapi import APIRouter, Query

router = APIRouter()

# Dynamically resolve base paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

BOARDGAMES_FILE = os.path.join(DATA_DIR, "boardgames.json")
CACHE_FILE = os.path.join(DATA_DIR, "cache.json")
CACHE_TTL = 60 * 60 * 24 * 7

def load_cache():
    if not os.path.exists(CACHE_FILE): return {}
    with open(CACHE_FILE, "r") as f: return json.load(f)

def save_cache(cache):
    with open(CACHE_FILE, "w") as f: json.dump(cache, f, indent=2)

def generate_cache_key(min_players, max_players, complexity, themes):
    key = json.dumps({
        "min_players": min_players,
        "max_players": max_players,
        "complexity": sorted(complexity or []),
        "themes": sorted(themes or [])
    }, sort_keys=True)
    return hashlib.md5(key.encode()).hexdigest()

def classify_complexity(weight):
    return "light" if weight < 1.8 else "medium" if weight < 3 else "heavy"

def normalize_description(desc: str) -> str:
    return desc.replace("\n", " ").replace("&#10;", " ").strip()

def filter_results(data, min_players: int, max_players: int, complexity, themes):
    result = []
    for g in data:
        print(f"Checking {g['name']} → complexity: {g['complexity']}, themes: {g['themes']}")
        if min_players and max_players:
            if not any(p >= min_players and p <= max_players for p in g["players"]):
                continue

        if complexity:
            if g["complexity"].lower() not in [c.lower() for c in complexity]:
                continue

        if themes:
            game_themes = [t.lower() for t in g["themes"]]
            selected_themes = [t.lower() for t in themes]
            if not any(t in game_themes for t in selected_themes):
                continue

        g["description"] = normalize_description(g.get("description", ""))
        result.append(g)
    return result

def get_all_games():
    if not os.path.exists(BOARDGAMES_FILE): return []
    with open(BOARDGAMES_FILE, "r", encoding="utf-8") as f: return json.load(f)

def get_recommendations(min_players: int, max_players: int, complexity: Optional[List[str]], themes: Optional[List[str]]) -> List[dict]:
    cache = load_cache()
    key = generate_cache_key(min_players, max_players, complexity, themes)
    if key in cache and time.time() - cache[key]["timestamp"] < CACHE_TTL:
        return cache[key]["results"]
    all_games = get_all_games()
    results = filter_results(all_games, min_players, max_players, complexity, themes)
    cache[key] = {"timestamp": time.time(), "results": results}
    save_cache(cache)
    return results

@router.get("/themes")
def get_all_themes() -> List[str]:
    themes = set()
    for game in get_all_games():
        for theme in game.get("themes", []):
            themes.add(theme)
    return sorted(themes)

@router.get("/recommend")
def recommend(
    min_players: Optional[int] = Query(default=None),
    max_players: Optional[int] = Query(default=None),
    complexity: Optional[List[str]] = Query(default=None),
    themes: Optional[List[str]] = Query(default=None),
):
    return get_recommendations(min_players, max_players, complexity, themes)
