import os
import sys
# Automatically append backend folder to system paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from app.core.database import engine, Base
from app.core.config import settings
from app.api.router import router as api_router

# Create Database tables on launch
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TalentLens AI API",
    description="Explainable Candidate Intelligence Platform API",
    version="1.0.0"
)

# CORS configuration to support direct file loading or multi-port development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix="/api")

# Determine paths for frontend files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend"))

if os.path.exists(frontend_dir):
    # Serve index.html on root path
    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    # Mount static assets if directories exist
    if os.path.exists(os.path.join(frontend_dir, "css")):
        app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
    if os.path.exists(os.path.join(frontend_dir, "js")):
        app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")
else:
    @app.get("/")
    def serve_placeholder():
        return {"message": "TalentLens AI Backend Active. Frontend directory not found."}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
