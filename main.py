from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from recommender import router as recommender_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json

app = FastAPI()

# Add this middleware:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- allow all for dev; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(recommender_router)

@app.get("/settings")
def get_settings():
    with open("settings.json", "r", encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))
    
# Serve static files (index.html, etc.)
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")