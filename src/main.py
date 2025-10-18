from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.v1.api import api_v1_router


app = FastAPI(
    title="Water Flow Prediction API",
    version="1.0.0",
    description="API for Water Flow Prediction System",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)
    
    # Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
    # Include API router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
    
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Water Flow Prediction API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }
