import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import aiohttp
import sys

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Python path:", sys.path)

# Create the FastAPI app
app = FastAPI()

# Import after app creation to avoid circular imports
from api.websocket import setup_websocket

# Load environment variables
load_dotenv()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate required environment variables
required_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing_vars)}\n"
        "Please create a .env file with these variables."
    )

# Setup WebSocket routes
setup_websocket(app)

async def test_lm_studio():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://127.0.0.1:1234/v1/models") as response:
                if response.status == 200:
                    print("Successfully connected to LM Studio")
                    models = await response.json()
                    print("Available models:", [m["id"] for m in models["data"]])
                else:
                    print("Failed to connect to LM Studio")
    except Exception as e:
        print(f"Error connecting to LM Studio: {e}")

def main():
    """
    Main entry point for the So Long Sucker AI Battle application.
    """
    print("Starting So Long Sucker AI Battle server...")
    print("Make sure LM Studio is running locally at http://127.0.0.1:1234 with the required models:")
    print("- llama-3.2-3b-instruct")
    print("- qwen2-0.5b-instruct")
    
    # Test LM Studio connection
    asyncio.run(test_lm_studio())
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()