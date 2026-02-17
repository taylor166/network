"""
Main entry point for the Contact Management API server.
"""
import uvicorn
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
# Use explicit path to ensure .env is found regardless of working directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "contacts.api:app",
        host=host,
        port=port,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
