"""
Application service for email operations with importance analysis.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.domain.models import Email, AnalysisConfig, ImportanceLevel
from src.domain.services import EmailImportanceDomainService
from src.infrastructure.llm_service import OllamaLLMService
from src.infrastructure.json_repository import JsonEmailRepository
from src.gmail_client import GmailClient

logger = logging.getLogger(__name__)


class EmailApplicationService:
    """Application service orchestrating email operations."""
    
    def __init__(self, gmail_client: GmailClient = None, config: AnalysisConfig = None, data_file: str = "data/emails.json"):
        self.gmail_client = gmail_client
        self.config = config or AnalysisConfig()
        
        # Initialize services
        self.repository = JsonEmailRepository(data_file)
        self.llm_service = OllamaLLMService()
        self.domain_service = EmailImportanceDomainService(self.llm_service)
    
    def fetch_and_save_unread_emails(self, max_results: int = 50) -> List[Email]:
        """Fetch unread emails from Gmail and replace database with fresh batch."""
        if not self.gmail_client:
            raise ValueError("Gmail client required for fetching emails")
            
        # Fetch from Gmail
        gmail_emails = self.gmail_client.fetch_emails(
            max_results=max_results,
            query="is:unread"
        )
        
        # Convert to domain objects
        domain_emails = self.convert_to_domain_emails(gmail_emails)
        
        # Replace entire database with fresh unread emails
        self.repository.save_emails(domain_emails, replace=True)
        
        logger.info(f"Fetched and replaced database with {len(domain_emails)} fresh unread emails")
        return domain_emails
    
    def load_saved_emails(self) -> List[Email]:
        """Load emails from JSON database."""
        return self.repository.load_emails()
    
    def get_database_metadata(self) -> Dict[str, Any]:
        """Get metadata about the email database."""
        return self.repository.get_metadata()
    
    def convert_to_domain_emails(self, gmail_emails: List[Dict[str, Any]]) -> List[Email]:
        """Convert Gmail API response to domain Email objects."""
        domain_emails = []
        
        for email_data in gmail_emails:
            domain_email = Email(
                id=email_data['id'],
                thread_id=email_data['thread_id'],
                sender=email_data['sender'],
                subject=email_data['subject'],
                date=email_data['date'],
                text_body=email_data.get('text_body', ''),
                html_body=email_data.get('html_body', ''),
                snippet=email_data.get('snippet', ''),
                labels=email_data.get('labels', []),
                size_estimate=email_data.get('size_estimate', 0),
                attachments=email_data.get('attachments', [])
            )
            domain_emails.append(domain_email)
        
        return domain_emails
    
    async def analyze_saved_emails(self, batch_size: int = None, progress_callback=None) -> Dict[str, Any]:
        """Analyze saved emails and update the JSON database."""
        unanalyzed_emails = self.repository.get_unanalyzed_emails()
        
        if not unanalyzed_emails:
            logger.info("No unanalyzed emails found")
            return {'analyzed': 0, 'skipped': 0, 'errors': 0}
        
        batch_size = batch_size or self.config.max_batch_size
        analyzed_count = 0
        error_count = 0
        total_emails = len(unanalyzed_emails)
        
        logger.info(f"Starting analysis of {total_emails} unanalyzed emails")
        
        # Process in batches
        for i in range(0, len(unanalyzed_emails), batch_size):
            batch = unanalyzed_emails[i:i + batch_size]
            batch_num = i//batch_size + 1
            logger.info(f"Processing batch {batch_num}: {len(batch)} emails")
            
            for j, email in enumerate(batch):
                current_email_num = i + j + 1
                try:
                    # Update progress callback if provided
                    if progress_callback:
                        progress_callback(current_email_num, total_emails, email.subject[:50], "analyzing")
                    
                    # Analyze importance
                    importance_score = await self.llm_service.analyze_importance(email, self.config)
                    
                    # Optionally analyze summary
                    summary = None
                    if self.config.enable_summarization:
                        if progress_callback:
                            progress_callback(current_email_num, total_emails, email.subject[:50], "summarizing")
                        summary = await self.llm_service.summarize_email(email, self.config)
                    
                    # Update in database
                    if progress_callback:
                        progress_callback(current_email_num, total_emails, email.subject[:50], "saving")
                    
                    success = self.repository.update_email_analysis(email.id, importance_score, summary)
                    if success:
                        analyzed_count += 1
                        if progress_callback:
                            progress_callback(current_email_num, total_emails, email.subject[:50], "completed")
                    else:
                        error_count += 1
                        if progress_callback:
                            progress_callback(current_email_num, total_emails, email.subject[:50], "error")
                        
                except Exception as e:
                    logger.error(f"Error analyzing email {email.id}: {e}")
                    error_count += 1
                    if progress_callback:
                        progress_callback(current_email_num, total_emails, email.subject[:50], "error")
            
            # Small delay between batches
            if i + batch_size < len(unanalyzed_emails):
                await asyncio.sleep(0.5)
        
        result = {
            'analyzed': analyzed_count,
            'errors': error_count,
            'total_processed': len(unanalyzed_emails)
        }
        
        logger.info(f"Analysis complete: {analyzed_count} analyzed, {error_count} errors")
        return result
    
    async def analyze_emails_importance(self, emails: List[Email]) -> List[Email]:
        """Analyze emails for importance using LLM (legacy method)."""
        logger.info(f"Starting importance analysis for {len(emails)} emails")
        
        try:
            analyzed_emails = await self.domain_service.analysis_service.batch_analyze(
                emails, self.config
            )
            logger.info(f"Successfully analyzed {len(analyzed_emails)} emails")
            return analyzed_emails
        except Exception as e:
            logger.error(f"Error during email analysis: {e}")
            # Return original emails if analysis fails
            return emails
    
    def get_deletion_candidates(self, min_score: float = -2.0) -> List[Email]:
        """Get emails that are candidates for deletion from database."""
        return self.repository.get_deletion_candidates(min_score)
    
    async def get_deletion_recommendations(self, emails: List[Email]) -> Dict[str, List[Email]]:
        """Get email deletion recommendations (legacy method)."""
        return await self.domain_service.analyze_emails_for_deletion(emails, self.config)
    
    def get_importance_summary(self, emails: List[Email]) -> Dict[str, Any]:
        """Get summary statistics of email importance."""
        if not emails:
            return {}
        
        level_counts = {}
        total_analyzed = 0
        safe_to_delete_count = 0
        
        for email in emails:
            if email.importance_score:
                total_analyzed += 1
                level = email.importance_score.level.value
                level_counts[level] = level_counts.get(level, 0) + 1
                
                if email.is_safe_to_delete():
                    safe_to_delete_count += 1
        
        return {
            'total_emails': len(emails),
            'analyzed_emails': total_analyzed,
            'level_distribution': level_counts,
            'safe_to_delete': safe_to_delete_count,
            'analysis_coverage': round((total_analyzed / len(emails)) * 100, 1) if emails else 0
        }
    
    def format_emails_for_display(self, emails: List[Email]) -> List[Dict[str, Any]]:
        """Format emails for CLI display."""
        formatted_emails = []
        
        for email in emails:
            # Parse date for better display
            date_str = email.date
            try:
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_display = dt.strftime('%m/%d %H:%M')
                else:
                    date_display = date_str[:10]
            except:
                date_display = date_str[:10] if date_str else 'Unknown'
            
            # Clean sender name
            sender = email.sender
            if '<' in sender:
                sender = sender.split('<')[0].strip()
            
            # Importance info
            importance_info = {
                'level': 'UNKNOWN',
                'score': 0.0,
                'color': 'white'
            }
            
            if email.importance_score:
                importance_info = {
                    'level': email.importance_score.level.value,
                    'score': email.importance_score.score,
                    'color': self._get_importance_color(email.importance_score.level),
                    'safe_to_delete': email.importance_score.safe_to_delete,
                    'reasons': email.importance_score.reasons[:2]  # Show top 2 reasons
                }
            
            formatted_email = {
                'id': email.id,
                'date': date_display,
                'sender': sender[:25],
                'subject': email.subject[:50],
                'importance': importance_info,
                'summary': email.summary.summary if email.summary else None,
                'snippet': email.snippet[:100]
            }
            
            formatted_emails.append(formatted_email)
        
        return formatted_emails
    
    def _get_importance_color(self, level: ImportanceLevel) -> str:
        """Get color for importance level."""
        color_map = {
            ImportanceLevel.CRITICAL: 'bright_red',
            ImportanceLevel.HIGH: 'red',
            ImportanceLevel.MEDIUM: 'yellow',
            ImportanceLevel.LOW: 'blue',
            ImportanceLevel.SPAM: 'dim'
        }
        return color_map.get(level, 'white')
    
    def generate_deletion_summary(self, deleted_emails: List[Email]) -> Dict[str, Any]:
        """Generate a categorized summary of deleted emails."""
        if not deleted_emails:
            return {'total': 0, 'categories': {}}
        
        # Count by category
        category_counts = {}
        category_examples = {}
        total_size = 0
        
        for email in deleted_emails:
            if email.importance_score and email.importance_score.category:
                category = email.importance_score.category
            else:
                category = 'other'
            
            category_counts[category] = category_counts.get(category, 0) + 1
            total_size += email.size_estimate
            
            # Store examples (up to 3 per category)
            if category not in category_examples:
                category_examples[category] = []
            if len(category_examples[category]) < 3:
                category_examples[category].append({
                    'sender': email.sender.split('<')[0].strip() if '<' in email.sender else email.sender,
                    'subject': email.subject[:50] + ('...' if len(email.subject) > 50 else '')
                })
        
        # Create human-readable category names
        category_labels = {
            'promotional': 'promotional emails (sales, deals, marketing)',
            'newsletter': 'newsletters and subscriptions',
            'social': 'social media notifications',
            'automated': 'automated service notifications',
            'financial': 'financial notifications',
            'security': 'security-related emails',
            'personal': 'personal communications',
            'other': 'other emails'
        }
        
        # Format summary
        summary = {
            'total': len(deleted_emails),
            'total_size_mb': round(total_size / (1024 * 1024), 1) if total_size > 0 else 0,
            'categories': {}
        }
        
        for category, count in category_counts.items():
            summary['categories'][category] = {
                'count': count,
                'label': category_labels.get(category, f'{category} emails'),
                'examples': category_examples.get(category, [])
            }
        
        return summary
    
    def format_deletion_summary_for_display(self, summary: Dict[str, Any]) -> List[str]:
        """Format deletion summary for CLI display."""
        if summary['total'] == 0:
            return ["No emails were marked as read."]
        
        lines = [f"✅ Marked {summary['total']} emails as read:"]
        
        # Sort categories by count (descending)
        sorted_categories = sorted(
            summary['categories'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        for category, info in sorted_categories:
            count = info['count']
            label = info['label']
            lines.append(f"  • {count} {label}")
            
            # Show examples for large categories
            if count >= 5 and info['examples']:
                lines.append(f"    Examples: {', '.join([ex['sender'] for ex in info['examples'][:2]])}")
        
        if summary['total_size_mb'] > 0:
            lines.append(f"  • Estimated space savings: {summary['total_size_mb']} MB")
        
        return lines

    async def close(self):
        """Clean up resources."""
        if self.llm_service:
            await self.llm_service.close()