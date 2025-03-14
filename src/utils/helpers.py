"""
Helper Utilities

This module provides common utility functions for the MCP application.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, date

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("mcp")

class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles datetime objects.
    """
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def json_serialize(data: Any) -> str:
    """
    Serialize data to JSON string with custom encoder.
    
    Args:
        data: Data to serialize
        
    Returns:
        JSON string
    """
    return json.dumps(data, cls=CustomJSONEncoder)

def parse_json(json_str: str) -> Dict[str, Any]:
    """
    Parse JSON string to dictionary.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Parsed dictionary
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        return {}

def extract_email_metadata(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant metadata from an email.
    
    Args:
        email_data: Email data from Gmail API
        
    Returns:
        Dictionary with extracted metadata
    """
    return {
        "id": email_data.get("id"),
        "subject": email_data.get("subject", "No Subject"),
        "from": email_data.get("from", "Unknown"),
        "date": email_data.get("date"),
        "snippet": email_data.get("snippet", "")
    }

def extract_github_repo_metadata(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant metadata from a GitHub repository.
    
    Args:
        repo_data: Repository data from GitHub API
        
    Returns:
        Dictionary with extracted metadata
    """
    return {
        "name": repo_data.get("name"),
        "description": repo_data.get("description", "No description"),
        "url": repo_data.get("url"),
        "stars": repo_data.get("stars", 0),
        "open_issues": repo_data.get("open_issues", 0)
    }

def log_action(action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an action taken by the MCP.
    
    Args:
        action: Description of the action
        details: Optional details about the action
    """
    if details:
        logger.info(f"Action: {action} - Details: {json_serialize(details)}")
    else:
        logger.info(f"Action: {action}")

def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:.0f}m {remaining_seconds:.0f}s" 