"""
MCP API Router

This module defines the API endpoints for the MCP system.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Import services
from src.services.agent import AgentService
from src.services.gmail import GmailAgent
from src.services.github import GithubService
from src.services.openai import OpenAIService

# Create router
router = APIRouter()

# Define request and response models
class MCPRequest(BaseModel):
    """Model for MCP requests."""
    query: str
    context: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    """Model for MCP responses."""
    response: str
    actions_taken: List[str]
    data: Optional[Dict[str, Any]] = None

# Service instances
gmail_service = GmailAgent()
github_service = GithubService()
openai_service = OpenAIService()
agent_service = AgentService(gmail_service, github_service, openai_service)

@router.post("/query", response_model=MCPResponse)
async def process_query(request: MCPRequest):
    """
    Process a natural language query to the MCP system.
    
    The system will:
    1. Use OpenAI to understand the query
    2. Decide which services to use (Gmail, GitHub, etc.)
    3. Execute the necessary actions
    4. Return a comprehensive response
    """
    try:
        # Process the query using the agent service
        result = await agent_service.process_query(request.query, request.context)
        
        return MCPResponse(
            response=result["response"],
            actions_taken=result["actions_taken"],
            data=result.get("data")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.get("/services/status")
async def get_services_status():
    """Get the status of all integrated services."""
    try:
        gmail_status = await gmail_service.check_status()
        github_status = await github_service.check_status()
        openai_status = await openai_service.check_status()
        
        return {
            "gmail": gmail_status,
            "github": github_status,
            "openai": openai_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking services: {str(e)}") 