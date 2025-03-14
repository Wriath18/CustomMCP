"""
Gmail Service

This service handles interactions with the Gmail API.
"""

import os
import base64
import email
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText

import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GmailService:
    """
    Service for interacting with Gmail API.
    """
    
    def __init__(self):
        """Initialize the Gmail service."""
        self.service = None
        self.user_id = os.getenv("GMAIL_USER_EMAIL", "me")
        
    async def _get_service(self):
        """Get or create the Gmail API service."""
        if self.service is None:
            # Load credentials from environment variables
            client_id = os.getenv("GMAIL_CLIENT_ID")
            client_secret = os.getenv("GMAIL_CLIENT_SECRET")
            refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
            
            if not all([client_id, client_secret, refresh_token]):
                raise ValueError("Gmail API credentials not properly configured")
            
            # Create credentials
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=["https://www.googleapis.com/auth/gmail.readonly"]
            )
            
            # Refresh the token
            request = google.auth.transport.requests.Request()
            creds.refresh(request)
            
            # Build the service
            self.service = build("gmail", "v1", credentials=creds)
        
        return self.service
    
    async def check_status(self) -> Dict[str, Any]:
        """Check if the Gmail service is properly configured and accessible."""
        try:
            service = await self._get_service()
            # Try to get profile info as a simple API test
            profile = service.users().getProfile(userId=self.user_id).execute()
            return {
                "status": "connected",
                "email": profile.get("emailAddress"),
                "messages_total": profile.get("messagesTotal", 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for emails in Gmail using the provided query.
        
        Args:
            query: Gmail search query (e.g., "from:github.com")
            max_results: Maximum number of results to return
            
        Returns:
            List of email metadata
        """
        try:
            service = await self._get_service()
            
            # Execute the search
            result = service.users().messages().list(
                userId=self.user_id,
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = result.get("messages", [])
            
            # Get metadata for each message
            email_list = []
            for message in messages:
                msg = service.users().messages().get(
                    userId=self.user_id,
                    id=message["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"]
                ).execute()
                
                headers = msg["payload"]["headers"]
                email_data = {
                    "id": msg["id"],
                    "thread_id": msg["threadId"],
                    "subject": next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject"),
                    "from": next((h["value"] for h in headers if h["name"] == "From"), "Unknown"),
                    "date": next((h["value"] for h in headers if h["name"] == "Date"), "Unknown"),
                    "snippet": msg.get("snippet", "")
                }
                
                email_list.append(email_data)
                
            return email_list
            
        except HttpError as error:
            raise Exception(f"Gmail API error: {error}")
    
    async def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """
        Get the full content of an email.
        
        Args:
            email_id: The ID of the email to retrieve
            
        Returns:
            Email content including body and headers
        """
        try:
            service = await self._get_service()
            
            # Get the full message
            message = service.users().messages().get(
                userId=self.user_id,
                id=email_id,
                format="full"
            ).execute()
            
            # Extract headers
            headers = message["payload"]["headers"]
            email_data = {
                "id": message["id"],
                "thread_id": message["threadId"],
                "subject": next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject"),
                "from": next((h["value"] for h in headers if h["name"] == "From"), "Unknown"),
                "to": next((h["value"] for h in headers if h["name"] == "To"), "Unknown"),
                "date": next((h["value"] for h in headers if h["name"] == "Date"), "Unknown"),
                "body": self._get_email_body(message["payload"]),
                "labels": message.get("labelIds", [])
            }
            
            return email_data
            
        except HttpError as error:
            raise Exception(f"Gmail API error: {error}")
    
    def _get_email_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract the email body from the payload.
        
        Args:
            payload: The email payload from the Gmail API
            
        Returns:
            The email body as text
        """
        if "body" in payload and payload["body"].get("data"):
            # If the body is in the current part
            body_data = payload["body"]["data"]
            body_text = base64.urlsafe_b64decode(body_data).decode("utf-8")
            return body_text
            
        elif "parts" in payload:
            # If the body is in parts (multipart email)
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and part["body"].get("data"):
                    body_data = part["body"]["data"]
                    body_text = base64.urlsafe_b64decode(body_data).decode("utf-8")
                    return body_text
                    
            # If no text/plain part, try to get HTML content
            for part in payload["parts"]:
                if part["mimeType"] == "text/html" and part["body"].get("data"):
                    body_data = part["body"]["data"]
                    body_text = base64.urlsafe_b64decode(body_data).decode("utf-8")
                    return body_text
                    
            # If still no body found, recursively check nested parts
            for part in payload["parts"]:
                if "parts" in part:
                    body_text = self._get_email_body(part)
                    if body_text:
                        return body_text
        
        return "No readable content found in this email." 