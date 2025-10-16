import uvicorn
from dotenv import load_dotenv
from src import create_app

# Load environment variables
load_dotenv()

# Create FastAPI application
app = create_app()

# Run application
if __name__ == '__main__':
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
