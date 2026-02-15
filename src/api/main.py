"""
PLC-RAG FastAPI Application
Main entry point for the API server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.config.settings import get_settings
from src.api.routes import upload, generate, download, ask

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="PLC-RAG API",
    description="AI-powered PLC logic generation from CSV process definitions",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """API root - health check and info"""
    return {
        "message": "PLC-RAG API is running",
        "version": "0.1.0",
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.api_env,
        "llm_provider": settings.llm_provider,
        "vector_db_provider": settings.vector_db_provider,
    }


@app.get("/hello")
async def hello_world():
    """Hello World endpoint for Phase 0 testing"""
    return {
        "message": "Hello from PLC-RAG! 🤖⚡",
        "phase": "Phase 0 - Infrastructure Setup Complete",
        "next_steps": [
            "Upload CSV files",
            "Generate PLC logic",
            "Download L5X files",
        ],
    }


# Include routers
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(generate.router, prefix="/api/v1", tags=["generate"])
app.include_router(ask.router, prefix="/api/v1", tags=["ask"])  # Personalized assistant

# Import streaming ask route
from src.api.routes import ask_stream
app.include_router(ask_stream.router, prefix="/api/v1", tags=["ask-stream"])  # Streaming assistant

# app.include_router(download.router, prefix="/api/v1", tags=["download"])  # Phase 4


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True if settings.api_env == "development" else False,
        log_level=settings.log_level.lower(),
    )
