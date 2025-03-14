#!/usr/bin/env python3
"""
Custom MCP (Mission Control Panel) - Main Application

This is the entry point for the Custom MCP application, which integrates
Gmail, GitHub, and OpenAI to create an intelligent agentic system.
"""

import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Import API routers
from src.api.mcp import router as mcp_router

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Create FastAPI app
app = FastAPI(
    title="Custom MCP",
    description="An intelligent agentic system that integrates with Gmail and GitHub",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")

# Set up templates
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))

# Include routers
app.include_router(mcp_router, prefix="/api", tags=["MCP"])

# Root endpoint
@app.get("/")
async def root(request: Request):
    """Serve the main frontend page."""
    return templates.TemplateResponse("index.html", {"request": request})

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 9000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"Starting Custom MCP server on {host}:{port}")
    uvicorn.run("src.main:app", host=host, port=port, reload=debug) 