# --- Enhancements to recommender.py ---

import json, os, time, hashlib, requests, xmltodict
from typing import List, Optional
from fastapi import APIRouter, Query

CACHE_FILE = "cache.json"
CACHE_TTL = 60 * 60 * 24 * 7  # 7 days
router = APIRouter()

def load_cache():
    if not os.path.exists(CACHE_FILE): return {}
    with open(CACHE_FILE, "r") as f: return json.load(f)

def save_cache(cache):
    with open(CACHE_FILE, "w") as f: json.dump(cache, f, indent=2)

def generate_cache_key(players, complexity, themes):
    key = json.dumps({"players": players, "complexity": sorted(complexity or []), "themes": sorted(themes or [])}, sort_keys=True)
    return hashlib.md5(key.encode()).hexdigest()

def classify_complexity(weight):
    return "light" if weight < 1.8 else "medium" if weight < 3 else "heavy"

def normalize_description(desc: str) -> str:
    return desc.replace("\n", " ").replace("&#10;", " ").strip()

def filter_results(data, players, complexity, themes):
    result = []
    for g in data:
        print(f"Checking {g['name']} → complexity: {g['complexity']}, themes: {g['themes']}")
        if players not in g["players"]:
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
    if not os.path.exists("boardgames.json"): return []
    with open("boardgames.json") as f: return json.load(f)

def get_recommendations(players: int, complexity: Optional[List[str]], themes: Optional[List[str]]) -> List[dict]:
    cache = load_cache()
    key = generate_cache_key(players, complexity, themes)
    if key in cache and time.time() - cache[key]["timestamp"] < CACHE_TTL:
        return cache[key]["results"]
    all_games = get_all_games()
    results = filter_results(all_games, players, complexity, themes)
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
    players: int,
    complexity: Optional[List[str]] = Query(default=None),
    themes: Optional[List[str]] = Query(default=None)
):
    print("🔍 players:", players)
    print("🔍 complexity:", complexity)
    print("🔍 themes:", themes)
    return get_recommendations(players, complexity, themes)

