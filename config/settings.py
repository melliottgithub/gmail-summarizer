"""
Minimal configuration for Gmail unread email fetching
"""

import os
from typing import List
from dotenv import load_dotenv

class Settings:
    """Minimal settings for Gmail unread email fetching."""
    
    def __init__(self):
        """Initialize settings from environment variables."""
        
        # Load environment variables
        load_dotenv()
        
        # Gmail API Configuration (only what's needed)
        self.gmail_credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'config/credentials.json')
        self.gmail_token_path = os.getenv('GMAIL_TOKEN_PATH', 'config/token.json')
        
        # Validate configuration
        self._validate()
    
    def _validate(self):
        """Validate configuration settings."""
        if not os.path.exists(self.gmail_credentials_path):
            raise ValueError(f"Gmail credentials file not found: {self.gmail_credentials_path}")
    
    def get_gmail_scopes(self) -> List[str]:
        """Get required Gmail API scopes."""
        return [
            'openid',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
