from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class EmailMetadata(BaseModel):
    id : str
    thread_id: Optional[str] = None
    subject: str = "No Subject"
    from_address: str = Field(..., alias="from")
    date: Optional[str] = None
    snippet: Optional[str] = None


class EmailContent(BaseModel):
    id: str
    thread_id: Optional[str] = None
    subject: str = "No Subject"
    from_address: str = Field(..., alias="from")
    to_address: Optional[str] = Field(None, alias="to")
    date: Optional[str] = None
    body: str
    labels: List[str] = []

class GithubRepository(BaseModel):
    name: str
    description: Optional[str] = None
    url: str
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    language: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GithubIssue(BaseModel):
    number: int
    title: str
    state: str
    created_at: datetime
    updated_at: datetime
    url: str
    body: Optional[str] = None
    labels: List[str] = []

class GitHubAlert(BaseModel):
    package: str
    severity: str
    summary: str
    description: Optional[str] = None
    published_at: datetime
    url: str

class ActionStep(BaseModel):
    type: str
    params: Dict[str, Any]

class ActionPlan(BaseModel):
    steps: List[ActionStep]

class QueryResult(BaseModel):
    response: str
    actions_taken: List[str]
    data: Optional[Dict[str, Any]] = None 