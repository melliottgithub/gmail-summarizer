"""
Domain models for email importance analysis.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from datetime import datetime


class ImportanceLevel(Enum):
    """Email importance levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH" 
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SPAM = "SPAM"


@dataclass
class ImportanceScore:
    """Value object representing an email's importance score."""
    score: float
    level: ImportanceLevel
    reasons: List[str]
    safe_to_delete: bool
    safety_override: bool
    
    def __post_init__(self):
        """Validate score constraints."""
        if not isinstance(self.score, (int, float)):
            raise ValueError("Score must be numeric")
        if not isinstance(self.reasons, list):
            raise ValueError("Reasons must be a list")


@dataclass
class EmailSummary:
    """Value object representing an email summary."""
    summary: str
    key_points: List[str]
    sentiment: Optional[str] = None
    urgency_indicators: List[str] = None
    
    def __post_init__(self):
        if self.urgency_indicators is None:
            self.urgency_indicators = []


@dataclass
class Email:
    """Email entity with business logic."""
    id: str
    thread_id: str
    sender: str
    subject: str
    date: str
    text_body: str
    html_body: str
    snippet: str
    labels: List[str]
    size_estimate: int
    attachments: List[dict]
    
    # Analysis results
    importance_score: Optional[ImportanceScore] = None
    summary: Optional[EmailSummary] = None
    
    def is_high_priority(self) -> bool:
        """Check if email is high priority."""
        if not self.importance_score:
            return False
        return self.importance_score.level in [ImportanceLevel.CRITICAL, ImportanceLevel.HIGH]
    
    def is_safe_to_delete(self) -> bool:
        """Check if email is safe to delete."""
        if not self.importance_score:
            return False
        return self.importance_score.safe_to_delete and not self.importance_score.safety_override
    
    def has_summary(self) -> bool:
        """Check if email has been summarized."""
        return self.summary is not None
    
    def get_age_days(self) -> int:
        """Get email age in days."""
        try:
            email_date = datetime.fromisoformat(self.date.replace('Z', '+00:00'))
            return (datetime.now(email_date.tzinfo) - email_date).days
        except:
            return 0


@dataclass 
class AnalysisConfig:
    """Configuration for email analysis."""
    summarization_model: str = "qwen2.5-coder:32b"
    importance_model: str = "qwen2.5-coder:32b"
    vip_senders: List[str] = None
    vip_domains: List[str] = None
    importance_threshold: float = 5.0
    deletion_threshold: float = -2.0
    max_batch_size: int = 10
    enable_safety_override: bool = True
    enable_summarization: bool = False
    
    def __post_init__(self):
        if self.vip_senders is None:
            self.vip_senders = []
        if self.vip_domains is None:
            self.vip_domains = []