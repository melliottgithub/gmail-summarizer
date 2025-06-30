"""
Configuration management for Gmail Summarizer
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

class Settings:
    """Configuration settings manager."""
    
    def __init__(self, config_file: str = None):
        """Initialize settings from environment variables and config file."""
        
        # Load environment variables
        if config_file:
            load_dotenv(config_file)
        else:
            load_dotenv()  # Load from .env file
        
        # Gmail API Configuration
        self.gmail_credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'config/credentials.json')
        self.gmail_token_path = os.getenv('GMAIL_TOKEN_PATH', 'config/token.json')
        
        # AI Service Configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.anthropic_model = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
        
        # Email Processing Configuration
        self.default_days_back = int(os.getenv('DEFAULT_DAYS_BACK', '7'))
        self.max_emails_per_batch = int(os.getenv('MAX_EMAILS_PER_BATCH', '100'))
        self.relevance_threshold = float(os.getenv('RELEVANCE_THRESHOLD', '0.7'))
        
        # Storage Configuration
        self.database_path = os.getenv('DATABASE_PATH', 'data/emails.db')
        self.backup_enabled = os.getenv('BACKUP_ENABLED', 'true').lower() == 'true'
        self.backup_frequency_days = int(os.getenv('BACKUP_FREQUENCY_DAYS', '7'))
        
        # Filtering Configuration
        exclude_senders = os.getenv('EXCLUDE_SENDERS', 'noreply@,no-reply@,notifications@')
        self.exclude_senders = [s.strip() for s in exclude_senders.split(',') if s.strip()]
        
        exclude_subjects = os.getenv('EXCLUDE_SUBJECTS', 'unsubscribe,newsletter,promotional')
        self.exclude_subjects = [s.strip().lower() for s in exclude_subjects.split(',') if s.strip()]
        
        include_labels = os.getenv('INCLUDE_ONLY_LABELS', 'INBOX,IMPORTANT')
        self.include_only_labels = [s.strip() for s in include_labels.split(',') if s.strip()]
        
        # Summarization Configuration
        self.summary_max_length = int(os.getenv('SUMMARY_MAX_LENGTH', '200'))
        self.summary_style = os.getenv('SUMMARY_STYLE', 'bullet_points')
        self.include_metadata = os.getenv('INCLUDE_METADATA', 'true').lower() == 'true'
        
        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'logs/gmail_summarizer.log')
        
        # Validate configuration
        self._validate()
    
    def _validate(self):
        """Validate configuration settings."""
        errors = []
        
        # Check for required files
        if not os.path.exists(self.gmail_credentials_path):
            errors.append(f"Gmail credentials file not found: {self.gmail_credentials_path}")
        
        # Check for at least one AI API key
        if not self.openai_api_key and not self.anthropic_api_key:
            errors.append("At least one AI API key (OpenAI or Anthropic) must be configured")
        
        # Validate numeric values
        if self.relevance_threshold < 0 or self.relevance_threshold > 1:
            errors.append("RELEVANCE_THRESHOLD must be between 0 and 1")
        
        if self.default_days_back <= 0:
            errors.append("DEFAULT_DAYS_BACK must be positive")
        
        if self.max_emails_per_batch <= 0:
            errors.append("MAX_EMAILS_PER_BATCH must be positive")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI service configuration."""
        config = {}
        
        if self.openai_api_key:
            config['openai'] = {
                'api_key': self.openai_api_key,
                'model': self.openai_model
            }
        
        if self.anthropic_api_key:
            config['anthropic'] = {
                'api_key': self.anthropic_api_key,
                'model': self.anthropic_model
            }
        
        return config
    
    def get_gmail_scopes(self) -> List[str]:
        """Get required Gmail API scopes."""
        return [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email'
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive data)."""
        return {
            'gmail_credentials_path': self.gmail_credentials_path,
            'default_days_back': self.default_days_back,
            'max_emails_per_batch': self.max_emails_per_batch,
            'relevance_threshold': self.relevance_threshold,
            'database_path': self.database_path,
            'exclude_senders': self.exclude_senders,
            'exclude_subjects': self.exclude_subjects,
            'include_only_labels': self.include_only_labels,
            'summary_max_length': self.summary_max_length,
            'summary_style': self.summary_style,
            'include_metadata': self.include_metadata,
            'log_level': self.log_level,
            'log_file': self.log_file
        }
