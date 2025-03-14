import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self) -> Dict[str, Any]:
        self.host = os.getenv("HOST", '0.0.0.0')
        self.port = int(os.getenv('PORT', 8000))
        self.debug = os.getenv("DEBUG", 'False').lower() == 'true'

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gmail_client_id = os.getenv("GMAIL_CLIENT_ID")
        self.gmail_client_secret = os.getenv("GMAIL_CLIENT_SECRET")
        self.gmail_refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
        self.gmail_user_email = os.getenv("GMAIL_USER_EMAIL", "me")
        self.github_access_token = os.getenv("GITHUB_ACCESS_TOKEN")
        self.github_username = os.getenv("GITHUB_USERNAME")

        return {
            "server": {
                "host": self.host,
                "port": self.port,
                "debug": self.debug
            },
            "services": {
                "openai": bool(self.openai_api_key),
                "gmail": bool(self.gmail_client_id and self.gmail_client_secret and self.gmail_refresh_token),
                "github": bool(self.github_access_token)
            }
        }
        
    def validateConnections(self) -> Dict[str, Any]:

        validation = {
            "openai" : self.openai_api_key is not None,
            "gmail" : all([
                self.gmail_client_id,
                self.gmail_client_secret,
                self.gmail_refresh_token
            ]),
            "github" : self.github_access_token is not None
        }

        return {
            "valid" : all(validation.values()),
            "services" : validation
        }
    
    