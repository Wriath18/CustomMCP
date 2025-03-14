"""
OpenAI Service

This service handles interactions with the OpenAI API for decision-making
and response generation.
"""

import os
import json
from typing import Dict, List, Any, Optional

import openai

class OpenAIService:
    """
    Service for interacting with OpenAI API.
    """
    
    def __init__(self):
        """Initialize the OpenAI service."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
    async def _get_client(self):
        """Get or create the OpenAI API client."""
        if self.client is None:
            if not self.api_key:
                raise ValueError("OpenAI API key not properly configured")
            
            # Set up the client
            openai.api_key = self.api_key
            self.client = openai.OpenAI(api_key=self.api_key)
        
        return self.client
    
    async def check_status(self) -> Dict[str, Any]:
        """Check if the OpenAI service is properly configured and accessible."""
        try:
            client = await self._get_client()
            # Try a simple API call to check if the API key is valid
            models = client.models.list()
            return {
                "status": "connected",
                "available_models": [model.id for model in models.data[:5]]  # Just show first 5 models
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def create_action_plan(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an action plan based on the user's query.
        
        Args:
            query: The natural language query from the user
            context: Optional context information
            
        Returns:
            An action plan with steps to execute
        """
        client = await self._get_client()
        
        # Prepare the system message with instructions
        system_message = """
        You are an intelligent agent that creates action plans based on user queries.
        Your task is to analyze the query and decide which services and actions are needed to fulfill it.
        
        Available services and actions:
        
        1. Gmail Service:
           - search_gmail: Search for emails in Gmail
             Parameters:
               - query: The search query for Gmail (e.g., "from:github.com")
               - max_results: Maximum number of results to return (optional, default: 10)
           
           - get_email_content: Get the full content of an email
             Parameters:
               - email_id: The ID of the email to retrieve
        
        2. GitHub Service:
           - search_github_repos: Search for repositories on GitHub
             Parameters:
               - query: The search query for GitHub repositories (e.g., "user:username", "topic:machine-learning")
               - max_results: Maximum number of results to return (optional, default: 5)
           
           - get_repo_alerts: Get security alerts for a repository
             Parameters:
               - repo_name: The full name of the repository (e.g., "username/repo-name")
           
           - get_repo_issues: Get issues for a repository
             Parameters:
               - repo_name: The full name of the repository (e.g., "username/repo-name")
               - state: Issue state ("open", "closed", or "all") (optional, default: "open")
               
           - get_repo_structure: Get the file structure of a repository
             Parameters:
               - repo_name: The full name of the repository (e.g., "username/repo-name")
               - max_depth: Maximum depth to traverse (optional, default: 3)
               
           - get_repo_contents: Get contents of a specific path in a repository
             Parameters:
               - repo_name: The full name of the repository (e.g., "username/repo-name")
               - path: Path within the repository (optional, default: root directory)
        
        IMPORTANT GUIDELINES:
        1. For multi-step queries, first search for information, then process the results.
        2. When dealing with GitHub repositories mentioned in emails, first search Gmail, then extract repository names from the results.
           - The system will automatically extract repository information from email snippets, so you don't need to explicitly handle this.
           - If you need to get GitHub repository information from emails, just search Gmail first.
        3. For GitHub-related queries, you can omit the repo_name parameter in get_repo_alerts, get_repo_issues, get_repo_structure, and get_repo_contents if you've already searched Gmail.
           - The system will automatically use extracted repository names from emails.
        4. If you're not sure about a parameter value, it's better to skip that step than to provide incorrect values.
        5. Each step should have a "type" and "params" field.
        6. When asked about repository structure or file contents, include get_repo_structure or get_repo_contents steps in your plan.
        
        Your response should be a valid JSON object with the following structure:
        {
            "steps": [
                {
                    "type": "action_type",
                    "params": {
                        "param1": "value1",
                        "param2": "value2"
                    }
                }
            ]
        }
        """
        
        # Prepare the user message with the query and context
        user_message = f"Query: {query}"
        if context:
            user_message += f"\nContext: {json.dumps(context)}"
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        try:
            plan_text = response.choices[0].message.content.strip()
            plan = json.loads(plan_text)
            return plan
        except json.JSONDecodeError:
            # If the response is not valid JSON, create a default plan
            return {
                "steps": []
            }
    
    async def generate_response(self, query: str, data: Dict[str, Any]) -> str:
        """
        Generate a natural language response based on the query and collected data.
        
        Args:
            query: The original query from the user
            data: Data collected from various services
            
        Returns:
            A natural language response
        """
        client = await self._get_client()
        
        # Prepare the system message with instructions
        system_message = """
        You are an intelligent assistant that provides helpful responses based on data collected from various services.
        Your task is to analyze the data and provide a clear, concise, and informative response to the user's query.
        
        Focus on the most relevant information and present it in a structured and easy-to-understand format.
        If there are multiple pieces of information, organize them logically.
        If there are no relevant results or if there were errors during data collection, explain that to the user and suggest alternative approaches.
        
        When dealing with GitHub repositories:
        1. If repository information is available, include details like name, description, and URL.
        2. If repository alerts or issues are available, summarize them clearly.
        3. If no repository information was found, suggest ways the user could refine their query.
        4. If repository information was extracted from emails but couldn't be verified on GitHub, mention this.
        5. If repository structure information is available, present it in a clear, hierarchical format.
        6. For file structures, focus on the most important files and directories, especially those related to the query.
        
        When dealing with emails:
        1. Summarize the most relevant emails related to the query.
        2. If emails contain GitHub repository information, highlight that connection.
        3. Don't include sensitive information like email IDs or full message content unless specifically requested.
        4. If there were errors accessing email content, focus on the information that was successfully retrieved.
        
        Be helpful and informative, even if some data collection steps encountered errors.
        """
        
        # Prepare the user message with the query and data
        user_message = f"Query: {query}\n\nData: {json.dumps(data, indent=2)}"
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        )
        
        # Return the response
        return response.choices[0].message.content.strip() 