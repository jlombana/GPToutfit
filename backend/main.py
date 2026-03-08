"""FastAPI application entry point for GPToutfit.

Creates the FastAPI app, mounts routes, and configures middleware.

See TASK-08 and TASK-11 in docs/TASKS.md for implementation spec.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.api.routes_calendar import router as calendar_router
from backend.api.routes_user import router as user_router

app = FastAPI(title="GPToutfit")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(calendar_router)
app.include_router(user_router)

project_root = Path(__file__).resolve().parents[1]
app.mount("/images", StaticFiles(directory=str(project_root / "sample_clothes" / "sample_images_large")), name="product-images")
app.mount("/photos", StaticFiles(directory=str(project_root / "Photos")), name="photos")
app.mount("/js", StaticFiles(directory=str(project_root / "frontend" / "js")), name="js")
app.mount("/", StaticFiles(directory=str(project_root / "frontend"), html=True), name="frontend")
