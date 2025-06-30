"""
AI-powered email summarization
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EmailSummarizer:
    """AI-powered email summarization using various LLM providers."""
    
    def __init__(self, settings):
        """Initialize summarizer with settings."""
        self.settings = settings
        self.ai_config = settings.get_ai_config()
        
    def summarize_emails(self, emails: List[Dict[str, Any]], style: str = 'bullet_points') -> str:
        """
        Generate a summary of the provided emails.
        
        Args:
            emails: List of email dictionaries
            style: Summary style ('paragraph', 'bullet_points', 'keywords')
            
        Returns:
            Generated summary text
        """
        if not emails:
            return "No emails to summarize."
        
        # For MVP, provide a basic text-based summary
        # This will be enhanced with AI integration later
        return self._generate_basic_summary(emails, style)
    
    def _generate_basic_summary(self, emails: List[Dict[str, Any]], style: str) -> str:
        """Generate a basic summary without AI (MVP version)."""
        
        total_emails = len(emails)
        
        # Group emails by sender
        sender_counts = {}
        important_emails = []
        categories = {'work': 0, 'personal': 0, 'notifications': 0, 'promotions': 0, 'other': 0}
        
        for email in emails:
            sender = email.get('sender', 'Unknown')
            sender_domain = self._extract_domain(sender)
            sender_counts[sender_domain] = sender_counts.get(sender_domain, 0) + 1
            
            # Track categories
            category = email.get('category', 'other')
            categories[category] = categories.get(category, 0) + 1
            
            # Identify important emails (high relevance score)
            if email.get('relevance_score', 0) > 0.8:
                important_emails.append(email)
        
        # Generate summary based on style
        if style == 'bullet_points':
            return self._format_bullet_summary(total_emails, sender_counts, categories, important_emails)
        elif style == 'keywords':
            return self._format_keyword_summary(emails, sender_counts, categories)
        else:  # paragraph
            return self._format_paragraph_summary(total_emails, sender_counts, categories, important_emails)
    
    def _extract_domain(self, sender: str) -> str:
        """Extract domain from email sender."""
        try:
            if '@' in sender:
                # Extract email from "Name <email@domain.com>" format
                if '<' in sender and '>' in sender:
                    email_part = sender.split('<')[1].split('>')[0]
                else:
                    email_part = sender
                
                domain = email_part.split('@')[1]
                return domain
            return sender
        except Exception:
            return sender
    
    def _format_bullet_summary(self, total_emails: int, sender_counts: Dict[str, int], 
                              categories: Dict[str, int], important_emails: List[Dict[str, Any]]) -> str:
        """Format summary as bullet points."""
        summary_lines = [
            f"📧 **Email Summary ({total_emails} emails)**",
            "",
            "**📊 Overview:**"
        ]
        
        # Add category breakdown
        for category, count in categories.items():
            if count > 0:
                emoji = {'work': '💼', 'personal': '👤', 'notifications': '🔔', 
                        'promotions': '🏷️', 'other': '📄'}.get(category, '📄')
                summary_lines.append(f"• {emoji} {category.title()}: {count} emails")
        
        summary_lines.extend(["", "**📨 Top Senders:**"])
        
        # Add top senders
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for domain, count in top_senders:
            summary_lines.append(f"• {domain}: {count} email{'s' if count > 1 else ''}")
        
        # Add important emails
        if important_emails:
            summary_lines.extend(["", "**⭐ Important Emails:**"])
            for email in important_emails[:3]:  # Show top 3
                subject = email.get('subject', 'No Subject')[:50]
                sender = self._extract_domain(email.get('sender', 'Unknown'))
                summary_lines.append(f"• {subject}... (from {sender})")
        
        return "\n".join(summary_lines)
    
    def _format_paragraph_summary(self, total_emails: int, sender_counts: Dict[str, int], 
                                 categories: Dict[str, int], important_emails: List[Dict[str, Any]]) -> str:
        """Format summary as paragraph."""
        
        # Main overview
        summary = f"You received {total_emails} emails during this period. "
        
        # Category breakdown
        category_text = []
        for category, count in categories.items():
            if count > 0:
                category_text.append(f"{count} {category}")
        
        if category_text:
            summary += f"These included {', '.join(category_text)} emails. "
        
        # Top senders
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_senders:
            sender_text = ", ".join([f"{domain} ({count})" for domain, count in top_senders])
            summary += f"Most emails came from: {sender_text}. "
        
        # Important emails
        if important_emails:
            summary += f"There were {len(important_emails)} high-priority emails that may require your attention."
        
        return summary
    
    def _format_keyword_summary(self, emails: List[Dict[str, Any]], 
                               sender_counts: Dict[str, int], categories: Dict[str, int]) -> str:
        """Format summary as keywords."""
        keywords = []
        
        # Add category keywords
        for category, count in categories.items():
            if count > 0:
                keywords.append(f"{category}({count})")
        
        # Add top sender domains
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        for domain, count in top_senders:
            keywords.append(f"{domain}({count})")
        
        # Add subject keywords (extract common words)
        subject_words = {}
        for email in emails:
            subject = email.get('subject', '').lower()
            words = [word.strip('.,!?()[]') for word in subject.split() 
                    if len(word) > 3 and word not in ['from', 'your', 'this', 'that', 'with']]
            for word in words:
                subject_words[word] = subject_words.get(word, 0) + 1
        
        # Add top subject keywords
        top_words = sorted(subject_words.items(), key=lambda x: x[1], reverse=True)[:5]
        for word, count in top_words:
            if count > 1:  # Only include words that appear multiple times
                keywords.append(f"{word}({count})")
        
        return "Keywords: " + ", ".join(keywords)
    
    def _would_use_ai_summary(self, emails: List[Dict[str, Any]], style: str) -> str:
        """
        Placeholder for future AI integration.
        This method shows how AI summarization would be implemented.
        """
        # This is where you would integrate with OpenAI, Anthropic, etc.
        # Example structure:
        
        # Prepare email content for AI
        email_content = []
        for email in emails[:10]:  # Limit to prevent token overflow
            content = {
                'sender': email.get('sender', ''),
                'subject': email.get('subject', ''),
                'snippet': email.get('snippet', ''),
                'date': email.get('date', ''),
                'category': email.get('category', 'other')
            }
            email_content.append(content)
        
        # Prepare prompt based on style
        style_instructions = {
            'bullet_points': 'Format the summary as bullet points with clear categories',
            'paragraph': 'Write a concise paragraph summary',
            'keywords': 'Extract key themes and topics as comma-separated keywords'
        }
        
        prompt = f"""
        Please summarize the following emails in {style} format:
        {style_instructions.get(style, '')}
        
        Emails: {email_content}
        
        Focus on:
        - Important actions needed
        - Key communications
        - Patterns and trends
        - Urgent items
        """
        
        # This would be implemented with actual AI API calls:
        # if 'openai' in self.ai_config:
        #     return self._call_openai(prompt)
        # elif 'anthropic' in self.ai_config:
        #     return self._call_anthropic(prompt)
        
        return "AI summarization not yet implemented - using basic summary instead."
