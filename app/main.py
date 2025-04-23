from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.init_db import init_db
from app.api.v1.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 App is starting up...")
    init_db()
    yield
    print("💥 App is shutting down...")


app = FastAPI(lifespan=lifespan, title="AI Note-Taking App API")

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(api_router, prefix="/api/v1", tags=["v1"])
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "AINotes API base is running!"}
