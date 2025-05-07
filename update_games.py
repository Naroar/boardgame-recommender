
import requests
import time
import xmltodict
from bs4 import BeautifulSoup
import json

TOP_N_GAMES = 100
GAMES_PER_PAGE = 100
BGG_BROWSE_URL = "https://boardgamegeek.com/browse/boardgame/page/"
BGG_THING_API = "https://boardgamegeek.com/xmlapi2/thing"
CHUNK_SIZE = 20
API_DELAY = 5
OUTPUT_FILE = "boardgames.json"

def scrape_top_game_ids(n=TOP_N_GAMES) -> list:
    ids = set()
    pages = (n // GAMES_PER_PAGE) + 1
    for page in range(1, pages + 1):
        print(f"🔍 Scraping page {page}...")
        url = BGG_BROWSE_URL + str(page)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.select("a.primary")
        for link in links:
            href = link.get("href")
            if href and "/boardgame/" in href:
                try:
                    game_id = int(href.split("/")[2])
                    ids.add(game_id)
                except Exception as e:
                    print(f"⚠️ Failed to parse ID: {href} — {e}")
        time.sleep(1)
    return list(ids)[:n]

def fetch_game_metadata(game_ids: list) -> list:
    results = []
    for i in range(0, len(game_ids), CHUNK_SIZE):
        chunk = game_ids[i:i + CHUNK_SIZE]
        url = f"{BGG_THING_API}?id={','.join(map(str, chunk))}&stats=1"
        print(f"📦 Fetching metadata for games {i+1} to {i+len(chunk)}...")
        response = requests.get(url)
        if not response.ok or not response.text.startswith('<?xml'):
            print(f"❌ Bad response from BGG API:\n{response.status_code}\n{response.text[:500]}")
            continue
        try:
            data = xmltodict.parse(response.text)
            items = data.get("items", {}).get("item", [])
            if isinstance(items, dict):
                items = [items]
            for item in items:
                try:
                    name = item["name"]
                    if isinstance(name, list):
                        name = next(n["@value"] for n in name if n["@type"] == "primary")
                    else:
                        name = name["@value"]

                    min_players = int(item["minplayers"]["@value"])
                    max_players = int(item["maxplayers"]["@value"])
                    playing_time = int(item["playingtime"]["@value"])
                    weight = float(item["statistics"]["ratings"]["averageweight"]["@value"])
                    links = item.get("link", [])
                    ratings = item["statistics"]["ratings"]

                    average = float(ratings["average"]["@value"])
                    bayes = float(ratings["bayesaverage"]["@value"])
                    users_rated = int(ratings["usersrated"]["@value"])

                    if isinstance(links, dict):
                        links = [links]


                    themes = [l["@value"] for l in links if l["@type"] in ["boardgamemechanic", "boardgamecategory"]]

                    results.append({
                        "id": int(item["@id"]),
                        "name": name,
                        "players": list(range(min_players, max_players + 1)),
                        "time": playing_time,
                        "complexity": classify_complexity(weight),
                        "themes": themes,
                        "image": item.get("image"),
                        "thumbnail": item.get("thumbnail"),
                        "description": item.get("description"),
                            "ratings": {
                                "average": average,
                                "geek": bayes,
                                "users": users_rated
                            }
                    })
                except Exception as e:
                    print(f"⚠️ Error parsing game item: {e}")
        except Exception as e:
            print(f"❌ XML parsing error: {e}")
        time.sleep(API_DELAY)
    return results

def classify_complexity(weight: float) -> str:
    if weight < 1.8:
        return "light"
    elif weight < 3:
        return "medium"
    else:
        return "heavy"

def save_to_file(games: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(games)} games to {path}")

# Execute the full pipeline
ids = scrape_top_game_ids()
games = fetch_game_metadata(ids)
save_to_file(games, OUTPUT_FILE)
