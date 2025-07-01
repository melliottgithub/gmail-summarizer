"""
Gmail API client for retrieving emails
"""

import os
import pickle
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import logging

logger = logging.getLogger(__name__)

class GmailClient:
    """Gmail API client for email operations."""
    
    def __init__(self, settings):
        """Initialize Gmail client with settings."""
        self.settings = settings
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.settings.gmail_token_path):
            try:
                with open(self.settings.gmail_token_path, 'rb') as token:
                    creds = pickle.load(token)
                logger.info("Loaded existing credentials from token file")
            except Exception as e:
                logger.warning(f"Failed to load existing token: {e}")
                # Remove corrupted token file
                try:
                    os.remove(self.settings.gmail_token_path)
                    logger.info("Removed corrupted token file")
                except Exception:
                    pass
                creds = None
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Attempting to refresh expired credentials")
                    creds.refresh(Request())
                    logger.info("Successfully refreshed credentials")
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    # Remove invalid token file
                    try:
                        os.remove(self.settings.gmail_token_path)
                        logger.info("Removed invalid token file")
                    except Exception:
                        pass
                    creds = None
            
            if not creds:
                if not os.path.exists(self.settings.gmail_credentials_path):
                    raise FileNotFoundError(
                        f"Gmail credentials file not found: {self.settings.gmail_credentials_path}. "
                        "Please download it from Google Cloud Console."
                    )
                
                logger.info("Starting OAuth flow for new credentials")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.settings.gmail_credentials_path,
                    self.settings.get_gmail_scopes()
                )
                # Force account selection by not using any cached login
                try:
                    creds = flow.run_local_server(
                        port=0, 
                        access_type='offline', 
                        prompt='consent'  # Force consent screen to avoid scope issues
                    )
                    logger.info("OAuth flow completed successfully")
                except Exception as e:
                    logger.error(f"OAuth flow failed: {e}")
                    raise
            
            # Save the credentials for the next run
            try:
                os.makedirs(os.path.dirname(self.settings.gmail_token_path), exist_ok=True)
                with open(self.settings.gmail_token_path, 'wb') as token:
                    pickle.dump(creds, token)
                logger.info(f"Saved credentials to {self.settings.gmail_token_path}")
            except Exception as e:
                logger.warning(f"Failed to save credentials: {e}")
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail API authentication successful")
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return {
                'emailAddress': profile.get('emailAddress'),
                'messagesTotal': profile.get('messagesTotal'),
                'threadsTotal': profile.get('threadsTotal')
            }
        except HttpError as error:
            logger.error(f"Failed to get user info: {error}")
            raise
    
    def fetch_emails(self, 
                    start_date: datetime = None,
                    end_date: datetime = None,
                    max_results: int = 100,
                    query: str = None) -> List[Dict[str, Any]]:
        """
        Fetch emails from Gmail.
        
        Args:
            start_date: Start date for email search
            end_date: End date for email search
            max_results: Maximum number of emails to retrieve
            query: Gmail search query string
        
        Returns:
            List of email dictionaries
        """
        try:
            # Build search query
            search_query = self._build_search_query(start_date, end_date, query)
            logger.info(f"Searching with query: {search_query}")
            
            # Get message list
            messages = self._get_message_list(search_query, max_results)
            logger.info(f"Found {len(messages)} messages")
            
            # Fetch full message details
            emails = []
            for message in messages:
                try:
                    email_data = self._get_message_details(message['id'])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.warning(f"Failed to fetch message {message['id']}: {e}")
                    continue
            
            logger.info(f"Successfully retrieved {len(emails)} emails")
            return emails
            
        except HttpError as error:
            logger.error(f"Failed to fetch emails: {error}")
            raise
    
    def _build_search_query(self, start_date: datetime = None, 
                           end_date: datetime = None, 
                           query: str = None) -> str:
        """Build Gmail search query string."""
        query_parts = []
        
        # Add date filters
        if start_date:
            query_parts.append(f"after:{start_date.strftime('%Y/%m/%d')}")
        if end_date:
            query_parts.append(f"before:{end_date.strftime('%Y/%m/%d')}")
        
        # Add custom query
        if query:
            query_parts.append(query)
        
        # No label filtering for minimal version
        
        return " ".join(query_parts) if query_parts else ""
    
    def _get_message_list(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Get list of message IDs matching the query."""
        messages = []
        page_token = None
        
        while len(messages) < max_results:
            try:
                result = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=min(500, max_results - len(messages)),
                    pageToken=page_token
                ).execute()
                
                if 'messages' in result:
                    messages.extend(result['messages'])
                
                page_token = result.get('nextPageToken')
                if not page_token:
                    break
                    
            except HttpError as error:
                logger.error(f"Failed to get message list: {error}")
                break
        
        return messages[:max_results]
    
    def _get_message_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific message."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return self._parse_message(message)
            
        except HttpError as error:
            logger.error(f"Failed to get message details for {message_id}: {error}")
            return None
    
    def _parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message into standardized format."""
        headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
        
        # Extract basic information
        email_data = {
            'id': message['id'],
            'thread_id': message['threadId'],
            'labels': message.get('labelIds', []),
            'date': self._parse_date(headers.get('Date', '')),
            'sender': headers.get('From', ''),
            'recipient': headers.get('To', ''),
            'subject': headers.get('Subject', ''),
            'cc': headers.get('Cc', ''),
            'bcc': headers.get('Bcc', ''),
            'reply_to': headers.get('Reply-To', ''),
            'message_id': headers.get('Message-ID', ''),
            'in_reply_to': headers.get('In-Reply-To', ''),
            'references': headers.get('References', ''),
        }
        
        # Extract body content
        body_data = self._extract_body(message['payload'])
        email_data.update(body_data)
        
        # Add metadata
        email_data['size_estimate'] = message.get('sizeEstimate', 0)
        email_data['snippet'] = message.get('snippet', '')
        
        return email_data
    
    def _extract_body(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text and HTML body from message payload."""
        text_body = ""
        html_body = ""
        attachments = []
        
        def extract_parts(part):
            nonlocal text_body, html_body, attachments
            
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain' and 'data' in part.get('body', {}):
                text_body += self._decode_body_data(part['body']['data'])
            elif mime_type == 'text/html' and 'data' in part.get('body', {}):
                html_body += self._decode_body_data(part['body']['data'])
            elif part.get('filename'):
                # Handle attachments
                attachments.append({
                    'filename': part['filename'],
                    'mime_type': mime_type,
                    'size': part.get('body', {}).get('size', 0)
                })
            
            # Recursively process parts
            if 'parts' in part:
                for subpart in part['parts']:
                    extract_parts(subpart)
        
        extract_parts(payload)
        
        return {
            'text_body': text_body.strip(),
            'html_body': html_body.strip(),
            'attachments': attachments
        }
    
    def _decode_body_data(self, data: str) -> str:
        """Decode base64url encoded body data."""
        try:
            # Gmail uses base64url encoding
            decoded_bytes = base64.urlsafe_b64decode(data + '==')
            return decoded_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Failed to decode body data: {e}")
            return ""
    
    def _parse_date(self, date_str: str) -> str:
        """Parse email date string to ISO format."""
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return date_str
    
    def get_labels(self) -> List[Dict[str, Any]]:
        """Get all available labels in the Gmail account."""
        try:
            result = self.service.users().labels().list(userId='me').execute()
            return result.get('labels', [])
        except HttpError as error:
            logger.error(f"Failed to get labels: {error}")
            return []
