

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """
    Settings class for managing application configuration.
    """
    
    def __init__(self):
        """Initialize settings from environment variables."""
        # Server settings
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        
        # API keys and credentials
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Gmail settings
        self.gmail_client_id = os.getenv("GMAIL_CLIENT_ID")
        self.gmail_client_secret = os.getenv("GMAIL_CLIENT_SECRET")
        self.gmail_refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
        self.gmail_user_email = os.getenv("GMAIL_USER_EMAIL", "me")
        
        # GitHub settings
        self.github_access_token = os.getenv("GITHUB_ACCESS_TOKEN")
        self.github_username = os.getenv("GITHUB_USERNAME")
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate that all required settings are present.
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            "openai": self.openai_api_key is not None,
            "gmail": all([
                self.gmail_client_id,
                self.gmail_client_secret,
                self.gmail_refresh_token
            ]),
            "github": self.github_access_token is not None
        }
        
        return {
            "valid": all(validation.values()),
            "services": validation
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to a dictionary.
        
        Returns:
            Dictionary representation of settings
        """
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

# Create a global settings instance
settings = Settings() 