"""
JSON-based email repository for persistence.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from domain.models import Email, ImportanceScore, EmailSummary, ImportanceLevel

logger = logging.getLogger(__name__)


class JsonEmailRepository:
    """JSON file-based email repository."""
    
    def __init__(self, data_file: str = "data/emails.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        if self.data_dir and not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
    
    def save_emails(self, emails: List[Email], replace: bool = True) -> None:
        """Save emails to JSON file."""
        try:
            # Load existing data if not replacing
            if not replace and os.path.exists(self.data_file):
                data = self._load_data()
                existing_emails = {email['id']: email for email in data.get('emails', [])}
            else:
                existing_emails = {}
            
            # Convert domain emails to dict format
            email_dicts = []
            for email in emails:
                email_dict = self._email_to_dict(email)
                existing_emails[email.id] = email_dict
            
            # Prepare data structure
            data = {
                'metadata': {
                    'last_sync': datetime.now().isoformat(),
                    'total_emails': len(existing_emails),
                    'analyzed_count': sum(1 for e in existing_emails.values() if e.get('analysis'))
                },
                'emails': list(existing_emails.values())
            }
            
            # Write to file atomically
            temp_file = self.data_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            os.rename(temp_file, self.data_file)
            
            logger.info(f"Saved {len(emails)} emails to {self.data_file}")
            
        except Exception as e:
            logger.error(f"Error saving emails to JSON: {e}")
            # Clean up temp file if it exists
            temp_file = self.data_file + '.tmp'
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise
    
    def load_emails(self) -> List[Email]:
        """Load emails from JSON file."""
        try:
            if not os.path.exists(self.data_file):
                logger.info("No email data file found, returning empty list")
                return []
            
            data = self._load_data()
            emails = []
            
            for email_dict in data.get('emails', []):
                email = self._dict_to_email(email_dict)
                emails.append(email)
            
            logger.info(f"Loaded {len(emails)} emails from {self.data_file}")
            return emails
            
        except Exception as e:
            logger.error(f"Error loading emails from JSON: {e}")
            return []
    
    def update_email_analysis(self, email_id: str, importance_score: ImportanceScore, summary: EmailSummary = None) -> bool:
        """Update analysis results for a specific email."""
        try:
            if not os.path.exists(self.data_file):
                logger.warning("No email data file found for update")
                return False
            
            data = self._load_data()
            emails = data.get('emails', [])
            
            # Find and update the email
            updated = False
            for email_dict in emails:
                if email_dict['id'] == email_id:
                    email_dict['analysis'] = {
                        'importance_score': importance_score.score,
                        'level': importance_score.level.value,
                        'safe_to_delete': importance_score.safe_to_delete,
                        'safety_override': importance_score.safety_override,
                        'reasons': importance_score.reasons,
                        'analyzed_at': datetime.now().isoformat()
                    }
                    
                    if summary:
                        email_dict['summary'] = {
                            'summary': summary.summary,
                            'key_points': summary.key_points,
                            'sentiment': summary.sentiment,
                            'urgency_indicators': summary.urgency_indicators
                        }
                    
                    updated = True
                    break
            
            if updated:
                # Update metadata
                data['metadata']['analyzed_count'] = sum(1 for e in emails if e.get('analysis'))
                data['metadata']['last_analysis'] = datetime.now().isoformat()
                
                # Save updated data
                temp_file = self.data_file + '.tmp'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                os.rename(temp_file, self.data_file)
                logger.info(f"Updated analysis for email {email_id}")
            else:
                logger.warning(f"Email {email_id} not found for update")
            
            return updated
            
        except Exception as e:
            logger.error(f"Error updating email analysis: {e}")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the email database."""
        try:
            if not os.path.exists(self.data_file):
                return {}
            
            data = self._load_data()
            return data.get('metadata', {})
            
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            return {}
    
    def get_unanalyzed_emails(self) -> List[Email]:
        """Get emails that haven't been analyzed yet."""
        emails = self.load_emails()
        return [email for email in emails if not email.importance_score]
    
    def get_deletion_candidates(self, min_score: float = -2.0) -> List[Email]:
        """Get emails that are candidates for deletion."""
        emails = self.load_emails()
        candidates = []
        
        for email in emails:
            if (email.importance_score and
                email.importance_score.safe_to_delete and
                email.importance_score.score <= min_score and
                not email.importance_score.safety_override):
                candidates.append(email)
        
        return candidates
    
    def _load_data(self) -> Dict[str, Any]:
        """Load raw data from JSON file."""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _email_to_dict(self, email: Email) -> Dict[str, Any]:
        """Convert Email domain object to dictionary."""
        email_dict = {
            'id': email.id,
            'thread_id': email.thread_id,
            'sender': email.sender,
            'subject': email.subject,
            'date': email.date,
            'text_body': email.text_body,
            'html_body': email.html_body,
            'snippet': email.snippet,
            'labels': email.labels,
            'size_estimate': email.size_estimate,
            'attachments': email.attachments,
            'saved_at': datetime.now().isoformat()
        }
        
        # Add analysis if available
        if email.importance_score:
            email_dict['analysis'] = {
                'importance_score': email.importance_score.score,
                'level': email.importance_score.level.value,
                'safe_to_delete': email.importance_score.safe_to_delete,
                'safety_override': email.importance_score.safety_override,
                'reasons': email.importance_score.reasons,
                'analyzed_at': datetime.now().isoformat()
            }
        
        # Add summary if available
        if email.summary:
            email_dict['summary'] = {
                'summary': email.summary.summary,
                'key_points': email.summary.key_points,
                'sentiment': email.summary.sentiment,
                'urgency_indicators': email.summary.urgency_indicators
            }
        
        return email_dict
    
    def _dict_to_email(self, email_dict: Dict[str, Any]) -> Email:
        """Convert dictionary to Email domain object."""
        # Create base email
        email = Email(
            id=email_dict['id'],
            thread_id=email_dict['thread_id'],
            sender=email_dict['sender'],
            subject=email_dict['subject'],
            date=email_dict['date'],
            text_body=email_dict.get('text_body', ''),
            html_body=email_dict.get('html_body', ''),
            snippet=email_dict.get('snippet', ''),
            labels=email_dict.get('labels', []),
            size_estimate=email_dict.get('size_estimate', 0),
            attachments=email_dict.get('attachments', [])
        )
        
        # Add analysis if available
        analysis = email_dict.get('analysis')
        if analysis:
            email.importance_score = ImportanceScore(
                score=analysis['importance_score'],
                level=ImportanceLevel(analysis['level']),
                safe_to_delete=analysis['safe_to_delete'],
                safety_override=analysis['safety_override'],
                reasons=analysis['reasons']
            )
        
        # Add summary if available
        summary_data = email_dict.get('summary')
        if summary_data:
            email.summary = EmailSummary(
                summary=summary_data['summary'],
                key_points=summary_data['key_points'],
                sentiment=summary_data.get('sentiment'),
                urgency_indicators=summary_data.get('urgency_indicators', [])
            )
        
        return email