import os
import logging
import base64
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText

import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GmailAgent:
    def __init__(self):
        self.service = None
        self.user_id = os.getenv("GMAIL_USER_EMAIL", "me")

    async def _get_service(self):
        if self.service is None:

            client_id = os.getenv("GMAIL_CLIENT_ID")
            client_secret = os.getenv("GMAIL_CLIENT_SECRET")
            refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

            if not all([client_id, client_secret, refresh_token]):
                raise ValueError("Gmail API credentials not properly configured")
            
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=["https://www.googleapis.com/auth/gmail.readonly"]
            )

            request = google.auth.transport.requests.Request()
            creds.refresh(request)

            self.service = build("gmail", "v1", credentials=creds)
        
        return self.service
        
    async def check_status(self) -> Dict[str, Any]:
        try:
            service = await self._get_service()
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
        try:
            service = await self._get_service()
            result = service.users().messages().list(
                userId=self.user_id,
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = result.get("messages", [])

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
        try:
            service = await self._get_service()
            message = service.users().messages().get(
                userId=self.user_id,
                id=email_id,
                format="full"
            ).execute()

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
        if "body" in payload and payload["body"].get("data"):
            # If the body is in the current part
            body_data = payload["body"]["data"]
            body_text = base64.urlsafe_b64decode(body_data).decode("utf-8")
            return body_text
        
        elif "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and part["body"].get("data"):
                    body_data = part["body"]["data"]
                    body_text = base64.urlsafe_b64decode(body_data).decode("utf-8")
                    return body_text

            for part in payload["parts"]:
                if part["mimeType"] == "text/html" and part["body"].get("data"):
                    body_data = part["body"]["data"]
                    body_text = base64.urlsafe_b64decode(body_data).decode("utf-8")
                    return body_text

            for part in payload["parts"]:
                if "parts" in part:
                    body_text = self._get_email_body(part)
                    if body_text:
                        return body_text
        
        return "No readable content found in this email."   
            
                
                
                