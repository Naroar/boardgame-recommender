from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from .recommender import router as recommender_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import json, os

# Determine if running in production
IS_PROD = os.environ.get("ENV") == "production"
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# CORS settings
if IS_PROD:
    allowed_origins = ["https://your-production-frontend.com"]
else:
    allowed_origins = ["http://localhost", "http://localhost:8000"]
print("Running from:", os.getcwd())
print("Expecting data at:", os.path.join(DATA_DIR, "settings.json"))
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(recommender_router, prefix="/api")

# Settings endpoint for frontend (used to load player count list)
@app.get("/data/settings", response_class=JSONResponse)
def get_settings():
    path = os.path.join(DATA_DIR, "settings.json")
    if not os.path.exists(path):
        return {"player_counts": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
# Mount static frontend files
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")