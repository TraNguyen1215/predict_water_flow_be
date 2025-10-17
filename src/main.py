from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.v1.api import api_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API for Water Flow Prediction System",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
    
    # Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
    # Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)
    
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Water Flow Prediction API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc"    
    }
