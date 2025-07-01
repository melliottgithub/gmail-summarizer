"""
Domain services for email importance analysis.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import Email, ImportanceScore, EmailSummary, AnalysisConfig


class EmailAnalysisService(ABC):
    """Abstract service for email analysis."""
    
    @abstractmethod
    async def analyze_importance(self, email: Email, config: AnalysisConfig) -> ImportanceScore:
        """Analyze email importance and return score."""
        pass
    
    @abstractmethod
    async def summarize_email(self, email: Email, config: AnalysisConfig) -> EmailSummary:
        """Summarize email content."""
        pass
    
    @abstractmethod
    async def batch_analyze(self, emails: List[Email], config: AnalysisConfig) -> List[Email]:
        """Analyze multiple emails efficiently."""
        pass


class EmailImportanceDomainService:
    """Domain service for email importance business logic."""
    
    def __init__(self, analysis_service: EmailAnalysisService):
        self.analysis_service = analysis_service
    
    async def analyze_emails_for_deletion(
        self, 
        emails: List[Email], 
        config: AnalysisConfig
    ) -> Dict[str, List[Email]]:
        """
        Analyze emails and categorize them for deletion decisions.
        
        Returns:
            Dict with 'safe_to_delete', 'review_required', 'keep' categories
        """
        analyzed_emails = await self.analysis_service.batch_analyze(emails, config)
        
        categories = {
            'safe_to_delete': [],
            'review_required': [],
            'keep': []
        }
        
        for email in analyzed_emails:
            if not email.importance_score:
                categories['review_required'].append(email)
            elif email.is_safe_to_delete() and email.importance_score.score < config.deletion_threshold:
                categories['safe_to_delete'].append(email)
            elif email.is_high_priority():
                categories['keep'].append(email)
            else:
                categories['review_required'].append(email)
        
        return categories
    
    def get_deletion_candidates(
        self, 
        emails: List[Email], 
        min_score: float = -5.0
    ) -> List[Email]:
        """Get emails that are safe candidates for deletion."""
        candidates = []
        
        for email in emails:
            if (email.importance_score and 
                email.is_safe_to_delete() and
                email.importance_score.score <= min_score and
                not email.importance_score.safety_override):
                candidates.append(email)
        
        return candidates
    
    def validate_deletion_safety(self, email: Email) -> Dict[str, Any]:
        """Validate if an email is truly safe to delete."""
        if not email.importance_score:
            return {'safe': False, 'reason': 'No importance analysis available'}
        
        if email.importance_score.safety_override:
            return {'safe': False, 'reason': 'Safety override activated'}
        
        if not email.importance_score.safe_to_delete:
            return {'safe': False, 'reason': 'Marked as not safe to delete'}
        
        # Additional business rules
        if any(keyword in email.subject.lower() for keyword in ['security', 'account', 'password']):
            return {'safe': False, 'reason': 'Contains security-related keywords'}
        
        if email.get_age_days() < 1:
            return {'safe': False, 'reason': 'Email is too recent'}
        
        return {'safe': True, 'reason': 'Passed all safety checks'}