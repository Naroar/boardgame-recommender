from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from recommender import router as recommender_router
from fastapi.middleware.cors import CORSMiddleware

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

# Serve static files (index.html, etc.)
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")