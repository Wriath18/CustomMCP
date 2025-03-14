"""
Data Models

This module defines the data models used in the MCP application.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class EmailMetadata(BaseModel):
    """Model for email metadata."""
    id: str
    thread_id: Optional[str] = None
    subject: str = "No Subject"
    from_address: str = Field(..., alias="from")
    date: Optional[str] = None
    snippet: Optional[str] = None

class EmailContent(BaseModel):
    """Model for email content."""
    id: str
    thread_id: Optional[str] = None
    subject: str = "No Subject"
    from_address: str = Field(..., alias="from")
    to_address: Optional[str] = Field(None, alias="to")
    date: Optional[str] = None
    body: str
    labels: List[str] = []

class GitHubRepository(BaseModel):
    """Model for GitHub repository information."""
    name: str
    description: Optional[str] = None
    url: str
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    language: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class GitHubIssue(BaseModel):
    """Model for GitHub issue information."""
    number: int
    title: str
    state: str
    created_at: datetime
    updated_at: datetime
    url: str
    body: Optional[str] = None
    labels: List[str] = []

class GitHubAlert(BaseModel):
    """Model for GitHub security alert information."""
    package: str
    severity: str
    summary: str
    description: Optional[str] = None
    published_at: datetime
    url: str

class ActionStep(BaseModel):
    """Model for an action step in a plan."""
    type: str
    params: Dict[str, Any]

class ActionPlan(BaseModel):
    """Model for an action plan."""
    steps: List[ActionStep]

class QueryResult(BaseModel):
    """Model for query results."""
    response: str
    actions_taken: List[str]
    data: Optional[Dict[str, Any]] = None 