"""
Email processing and filtering logic
"""

import re
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Process and filter emails based on relevance criteria."""
    
    def __init__(self, settings):
        """Initialize email processor with settings."""
        self.settings = settings
    
    def filter_emails(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter emails based on relevance criteria.
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            Filtered list of relevant emails
        """
        relevant_emails = []
        
        for email in emails:
            if self._is_relevant(email):
                # Add relevance score
                email['relevance_score'] = self._calculate_relevance_score(email)
                relevant_emails.append(email)
        
        # Sort by relevance score (highest first)
        relevant_emails.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        logger.info(f"Filtered {len(emails)} emails down to {len(relevant_emails)} relevant emails")
        return relevant_emails
    
    def _is_relevant(self, email: Dict[str, Any]) -> bool:
        """Check if email meets basic relevance criteria."""
        
        # Check sender filters
        if self._is_excluded_sender(email.get('sender', '')):
            return False
        
        # Check subject filters
        if self._is_excluded_subject(email.get('subject', '')):
            return False
        
        # Check if email has sufficient content
        if not self._has_sufficient_content(email):
            return False
        
        # Check relevance score threshold
        relevance_score = self._calculate_relevance_score(email)
        if relevance_score < self.settings.relevance_threshold:
            return False
        
        return True
    
    def _is_excluded_sender(self, sender: str) -> bool:
        """Check if sender should be excluded."""
        sender_lower = sender.lower()
        
        for exclude_pattern in self.settings.exclude_senders:
            if exclude_pattern.lower() in sender_lower:
                return True
        
        return False
    
    def _is_excluded_subject(self, subject: str) -> bool:
        """Check if subject should be excluded."""
        subject_lower = subject.lower()
        
        for exclude_pattern in self.settings.exclude_subjects:
            if exclude_pattern.lower() in subject_lower:
                return True
        
        return False
    
    def _has_sufficient_content(self, email: Dict[str, Any]) -> bool:
        """Check if email has sufficient content to be relevant."""
        
        # Check text body length
        text_body = email.get('text_body', '')
        if len(text_body.strip()) < 50:  # Minimum 50 characters
            return False
        
        # Check if it's not just an automated message
        automated_indicators = [
            'do not reply',
            'this is an automated',
            'no-reply',
            'unsubscribe',
            'automatically generated'
        ]
        
        text_lower = text_body.lower()
        automated_count = sum(1 for indicator in automated_indicators if indicator in text_lower)
        
        # If more than 2 automated indicators, likely not relevant
        if automated_count > 2:
            return False
        
        return True
    
    def _calculate_relevance_score(self, email: Dict[str, Any]) -> float:
        """
        Calculate relevance score for an email (0.0 to 1.0).
        
        Higher scores indicate more relevant emails.
        """
        score = 0.0
        
        # Base score for having content
        if email.get('text_body'):
            score += 0.3
        
        # Boost for important labels
        important_labels = ['IMPORTANT', 'STARRED', 'CATEGORY_PRIMARY']
        email_labels = email.get('labels', [])
        for label in important_labels:
            if label in email_labels:
                score += 0.2
        
        # Boost for personal emails (not automated)
        if self._is_personal_email(email):
            score += 0.3
        
        # Boost for recent emails
        score += self._calculate_recency_score(email)
        
        # Boost for emails with attachments (might be important documents)
        if email.get('attachments'):
            score += 0.1
        
        # Boost based on sender reputation
        score += self._calculate_sender_score(email.get('sender', ''))
        
        # Boost based on subject importance
        score += self._calculate_subject_score(email.get('subject', ''))
        
        # Normalize to 0.0-1.0 range
        return min(1.0, score)
    
    def _is_personal_email(self, email: Dict[str, Any]) -> bool:
        """Check if email appears to be personal rather than automated."""
        
        # Check for personal indicators in text
        text_body = email.get('text_body', '').lower()
        
        personal_indicators = [
            'hi ', 'hello ', 'hey ',
            'thanks', 'thank you',
            'please', 'could you',
            'let me know', 'get back to me',
            'meeting', 'call', 'schedule'
        ]
        
        personal_count = sum(1 for indicator in personal_indicators if indicator in text_body)
        
        # Check sender domain (personal emails often from common providers)
        sender = email.get('sender', '')
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com']
        has_personal_domain = any(domain in sender.lower() for domain in personal_domains)
        
        return personal_count >= 2 or has_personal_domain
    
    def _calculate_recency_score(self, email: Dict[str, Any]) -> float:
        """Calculate score bonus based on email recency."""
        try:
            email_date = datetime.fromisoformat(email.get('date', '').replace('Z', '+00:00'))
            now = datetime.now(email_date.tzinfo)
            days_old = (now - email_date).days
            
            # More recent emails get higher scores
            if days_old <= 1:
                return 0.2
            elif days_old <= 3:
                return 0.15
            elif days_old <= 7:
                return 0.1
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"Failed to calculate recency score: {e}")
            return 0.0
    
    def _calculate_sender_score(self, sender: str) -> float:
        """Calculate score based on sender characteristics."""
        score = 0.0
        
        # Known important senders (you can customize this)
        important_keywords = [
            'manager', 'director', 'ceo', 'president',
            'hr', 'human resources', 'admin',
            'support', 'team', 'project'
        ]
        
        sender_lower = sender.lower()
        for keyword in important_keywords:
            if keyword in sender_lower:
                score += 0.05
        
        # Avoid obvious spam/marketing senders
        spam_keywords = [
            'marketing', 'promotions', 'deals',
            'newsletter', 'updates', 'notification'
        ]
        
        for keyword in spam_keywords:
            if keyword in sender_lower:
                score -= 0.1
        
        return max(0.0, score)
    
    def _calculate_subject_score(self, subject: str) -> float:
        """Calculate score based on subject line importance."""
        score = 0.0
        
        # Important subject keywords
        important_keywords = [
            'urgent', 'asap', 'deadline', 'meeting',
            'interview', 'offer', 'contract', 'agreement',
            'project', 'update', 'status', 'report',
            'question', 'help', 'issue', 'problem'
        ]
        
        subject_lower = subject.lower()
        for keyword in important_keywords:
            if keyword in subject_lower:
                score += 0.05
        
        # Reduce score for promotional subjects
        promo_keywords = [
            'sale', 'discount', 'offer', 'deal',
            'free', 'win', 'congratulations',
            'newsletter', 'update', 'news'
        ]
        
        for keyword in promo_keywords:
            if keyword in subject_lower:
                score -= 0.05
        
        return max(0.0, score)
    
    def categorize_emails(self, emails: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize emails into different types."""
        categories = {
            'work': [],
            'personal': [],
            'notifications': [],
            'promotions': [],
            'other': []
        }
        
        for email in emails:
            category = self._determine_category(email)
            categories[category].append(email)
        
        return categories
    
    def _determine_category(self, email: Dict[str, Any]) -> str:
        """Determine the category of an email."""
        subject = email.get('subject', '').lower()
        sender = email.get('sender', '').lower()
        text_body = email.get('text_body', '').lower()
        
        # Work-related keywords
        work_keywords = [
            'meeting', 'project', 'deadline', 'report',
            'team', 'office', 'manager', 'client',
            'proposal', 'contract', 'business'
        ]
        
        if any(keyword in subject or keyword in text_body for keyword in work_keywords):
            return 'work'
        
        # Notification keywords
        notification_keywords = [
            'notification', 'alert', 'reminder',
            'confirmation', 'receipt', 'invoice'
        ]
        
        if any(keyword in subject for keyword in notification_keywords):
            return 'notifications'
        
        # Promotional keywords
        promo_keywords = [
            'sale', 'discount', 'offer', 'deal',
            'promotion', 'newsletter', 'marketing'
        ]
        
        if any(keyword in subject for keyword in promo_keywords):
            return 'promotions'
        
        # Personal indicators
        if self._is_personal_email(email):
            return 'personal'
        
        return 'other'
