from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.init_db import init_databases
from app.api.auth import router as auth_router
from app.api.logistics import router as logistics_router
from app.api.finance import router as finance_router
from app.api.timeline import router as timeline_router
from app.api.inbox import router as inbox_router

STATIC_DIR = Path(__file__).resolve().parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite databases and seed default profiles
    init_databases()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Enable CORS for local/tunnel PWA access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(logistics_router)
app.include_router(finance_router)
app.include_router(timeline_router)
app.include_router(inbox_router)

# Mount static assets directory
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    """Serves the single page application shell."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Domus API running. Frontend assets not yet initialized."}

@app.get("/manifest.json")
def serve_manifest():
    """Serves the PWA web app manifest."""
    manifest_file = STATIC_DIR / "manifest.json"
    if manifest_file.exists():
        return FileResponse(manifest_file, media_type="application/manifest+json")
    return {"message": "Manifest not found"}

@app.get("/sw.js")
def serve_service_worker():
    """Serves the root Service Worker for PWA caching."""
    sw_file = STATIC_DIR / "sw.js"
    if sw_file.exists():
        return FileResponse(sw_file, media_type="application/javascript")
    return {"message": "Service Worker not found"}
