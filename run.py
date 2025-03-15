import os
import sys
import uvicorn
from dotenv import load_dotenv
load_dotenv()

def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"Starting Custom MCP server on {host}:{port}")
    print(f"Debug mode: {debug}")
    print("Press Ctrl+C to stop the server")
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=debug
    )

if __name__ == "__main__":
    main() 