#!/usr/bin/env python3
"""
Development server runner
Quick script to start the FastAPI server
"""
if __name__ == "__main__":
    from src.api.main import app, settings
    import uvicorn

    print("=" * 60)
    print("🚀 Starting PLC-RAG API Server")
    print("=" * 60)
    print(f"Environment: {settings.api_env}")
    print(f"Host: {settings.api_host}:{settings.api_port}")
    print(f"Docs: http://localhost:{settings.api_port}/docs")
    print(f"Health: http://localhost:{settings.api_port}/health")
    print("=" * 60)

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True if settings.api_env == "development" else False,
        log_level=settings.log_level.lower(),
    )
