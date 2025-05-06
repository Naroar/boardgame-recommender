import json, os, time, hashlib, requests, xmltodict
from typing import List, Optional

CACHE_FILE = "cache.json"
CACHE_TTL = 60 * 60 * 24 * 7  # 7 days
def load_cache():
    if not os.path.exists(CACHE_FILE): return {}
    with open(CACHE_FILE, "r") as f: return json.load(f)
def save_cache(cache):
    with open(CACHE_FILE, "w") as f: json.dump(cache, f, indent=2)
def generate_cache_key(players, complexity, themes):
    key = json.dumps({"players": players, "complexity": sorted(complexity or []), "themes": sorted(themes or [])}, sort_keys=True)
    return hashlib.md5(key.encode()).hexdigest()
def classify_complexity(weight): return "light" if weight < 1.8 else "medium" if weight < 3 else "heavy"
def filter_results(data, players, complexity, themes):
    result = []
    for g in data:
        if players not in g["players"]: continue
        if complexity and g["complexity"] not in complexity: continue
        if themes and not any(t in g["themes"] for t in themes): continue
        result.append(g)
    return result
def get_recommendations(players: int, complexity: Optional[List[str]], themes: Optional[List[str]]) -> List[dict]:
    cache = load_cache()
    key = generate_cache_key(players, complexity, themes)
    if key in cache and time.time() - cache[key]["timestamp"] < CACHE_TTL:
        return cache[key]["results"]
    if not os.path.exists("boardgames.json"): return []
    with open("boardgames.json") as f: all_games = json.load(f)
    results = filter_results(all_games, players, complexity, themes)
    cache[key] = {"timestamp": time.time(), "results": results}
    save_cache(cache)
    return results
