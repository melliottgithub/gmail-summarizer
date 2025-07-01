"""
LLM-based email analysis service using Ollama.
"""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime

from src.domain.models import Email, ImportanceScore, EmailSummary, ImportanceLevel, AnalysisConfig
from src.domain.services import EmailAnalysisService

logger = logging.getLogger(__name__)


class OllamaLLMService(EmailAnalysisService):
    """LLM service implementation using Ollama."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def analyze_importance(self, email: Email, config: AnalysisConfig) -> ImportanceScore:
        """Analyze email importance using LLM."""
        prompt = self._build_importance_prompt(email)
        
        try:
            response = await self._call_ollama(config.importance_model, prompt)
            return self._parse_importance_response(response, email)
        except Exception as e:
            logger.error(f"Error analyzing importance for email {email.id}: {e}")
            # Fallback to basic analysis
            return self._fallback_importance_analysis(email)
    
    async def summarize_email(self, email: Email, config: AnalysisConfig) -> EmailSummary:
        """Summarize email content using LLM."""
        prompt = self._build_summary_prompt(email)
        
        try:
            response = await self._call_ollama(config.summarization_model, prompt)
            return self._parse_summary_response(response)
        except Exception as e:
            logger.error(f"Error summarizing email {email.id}: {e}")
            return EmailSummary(
                summary=email.snippet[:100] + "..." if len(email.snippet) > 100 else email.snippet,
                key_points=[],
                sentiment="unknown"
            )
    
    async def batch_analyze(self, emails: List[Email], config: AnalysisConfig) -> List[Email]:
        """Analyze multiple emails efficiently."""
        analyzed_emails = []
        
        # Process in batches to avoid overwhelming the LLM
        batch_size = config.max_batch_size
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            
            # Analyze importance and summarization concurrently for each email
            tasks = []
            for email in batch:
                tasks.append(self._analyze_single_email(email, config))
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for email, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error analyzing email {email.id}: {result}")
                    # Keep original email without analysis
                    analyzed_emails.append(email)
                else:
                    analyzed_emails.append(result)
            
            # Small delay between batches to be nice to the LLM
            if i + batch_size < len(emails):
                await asyncio.sleep(0.5)
        
        return analyzed_emails
    
    async def _analyze_single_email(self, email: Email, config: AnalysisConfig) -> Email:
        """Analyze a single email (importance + summary)."""
        # Run importance analysis and summarization concurrently
        importance_task = self.analyze_importance(email, config)
        summary_task = self.summarize_email(email, config)
        
        importance_score, summary = await asyncio.gather(
            importance_task, summary_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(importance_score, Exception):
            logger.error(f"Importance analysis failed for {email.id}: {importance_score}")
            importance_score = self._fallback_importance_analysis(email)
        
        if isinstance(summary, Exception):
            logger.error(f"Summarization failed for {email.id}: {summary}")
            summary = EmailSummary(
                summary=email.snippet[:100] + "..." if len(email.snippet) > 100 else email.snippet,
                key_points=[]
            )
        
        # Create new email with analysis results
        email.importance_score = importance_score
        email.summary = summary
        
        return email
    
    async def _call_ollama(self, model: str, prompt: str) -> str:
        """Make API call to Ollama."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent analysis
                "top_p": 0.9,
                "num_predict": 300,
                "num_ctx": 2048
            }
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    
    def _build_importance_prompt(self, email: Email) -> str:
        """Build prompt for importance analysis."""
        return f"""
You are an ULTRA AGGRESSIVE email importance analyzer. Your goal is to RUTHLESSLY eliminate email trash. Be EXTREMELY harsh with ANY marketing content. Default to marking emails as trash unless they are clearly critical.

Email Details:
- From: {email.sender}
- Subject: {email.subject}
- Date: {email.date}
- Content: {email.text_body[:1000]}...

TRASH EMAIL CATEGORIES (mark as safe_to_delete=true, score 0.5-1):
- ANY marketing/promotional emails (sales, deals, newsletters, coupons, offers)
- ALL fitness/gym/wellness content (promotions, classes, memberships)
- ALL entertainment (Netflix, streaming, sports, concerts, events, shows)
- ALL shopping (Amazon, retail, flash sales, deals, product updates)
- ALL social media notifications (Facebook, LinkedIn, Twitter, Instagram)
- ALL travel promotions and deals (unless confirmed personal bookings)
- ALL restaurant/food delivery promotions and marketing
- ALL job board spam and generic recruiting (unless personally addressed)
- ALL real estate promotions, listings, and market updates  
- ALL insurance and loan offers/promotions
- ALL software/app promotional emails and feature updates
- ALL event invitations from marketing sources
- ALL webinar, course, and conference promotions
- ALL survey requests and feedback forms from companies
- ALL unsubscribe confirmations and email preferences
- ALL newsletters unless explicitly personal or critical
- ALL automated service updates from non-essential services
- ALL "updates" from social platforms, apps, or services
- ALL "recommendations" or "suggestions" from any platform

LOW PRIORITY TRASH (score 1-2, mark safe_to_delete=true):
- Company blog updates and newsletters
- Service feature announcements  
- Generic customer service templates
- Automated receipts for non-essential purchases
- App notifications and updates
- Platform policy updates
- Community forum notifications

KEEP EMAILS ONLY IF (score 7-10, safe_to_delete=false):
- Security alerts, password resets, 2FA codes, account breaches
- Banking, financial statements, payment confirmations, tax documents
- Medical communications, healthcare appointments, test results
- Direct personal communications from real humans (not templates)
- Confirmed travel bookings and reservations (actual tickets/confirmations)
- Legal documents, contracts, important deadlines
- Work-related communications from colleagues or clients
- Critical account notifications (suspensions, violations, required actions)

BE ULTRA AGGRESSIVE:
- ANY hint of marketing = score 0.5-1 and safe_to_delete=true
- If unsure whether it's promotional, mark it as trash (score 1)
- Only use safety_override=true for security/financial/medical/legal/personal
- Better to delete too much than too little - be RUTHLESS
- Newsletters, updates, notifications = almost always trash (score 1)
- "noreply" senders = almost always trash unless security/financial

Email categorization (add to reasons):
- "promotional" - marketing, sales, deals
- "newsletter" - subscriptions, updates
- "social" - social media notifications
- "automated" - system-generated notifications
- "personal" - direct human communications
- "financial" - banking, payments
- "security" - account security, passwords

Respond in this exact JSON format:
{{
    "importance_score": <number 1-10>,
    "importance_level": "<CRITICAL|HIGH|MEDIUM|LOW|SPAM>",
    "safe_to_delete": <true/false>,
    "safety_override": <true/false>,
    "reasons": ["category", "specific reason", "pattern identified"],
    "email_category": "<promotional|newsletter|social|automated|personal|financial|security|other>"
}}
"""
    
    def _build_summary_prompt(self, email: Email) -> str:
        """Build prompt for email summarization."""
        return f"""
Summarize this email concisely in 1-2 sentences and extract key points.

Email:
From: {email.sender}
Subject: {email.subject}
Content: {email.text_body[:2000]}

Respond in this exact JSON format:
{{
    "summary": "<1-2 sentence summary>",
    "key_points": ["point 1", "point 2", "point 3"],
    "sentiment": "<positive|negative|neutral|urgent>",
    "urgency_indicators": ["indicator 1", "indicator 2"]
}}
"""
    
    def _parse_importance_response(self, response: str, email: Email) -> ImportanceScore:
        """Parse LLM response for importance analysis."""
        try:
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return ImportanceScore(
                    score=float(data.get('importance_score', 5.0)),
                    level=ImportanceLevel(data.get('importance_level', 'MEDIUM')),
                    safe_to_delete=bool(data.get('safe_to_delete', False)),
                    safety_override=bool(data.get('safety_override', False)),
                    reasons=data.get('reasons', ['LLM analysis']),
                    category=data.get('email_category', 'other')
                )
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logger.warning(f"Failed to parse LLM importance response: {e}")
            return self._fallback_importance_analysis(email)
    
    def _parse_summary_response(self, response: str) -> EmailSummary:
        """Parse LLM response for summarization."""
        try:
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return EmailSummary(
                    summary=data.get('summary', 'Unable to summarize'),
                    key_points=data.get('key_points', []),
                    sentiment=data.get('sentiment', 'neutral'),
                    urgency_indicators=data.get('urgency_indicators', [])
                )
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logger.warning(f"Failed to parse LLM summary response: {e}")
            return EmailSummary(
                summary="Unable to generate summary",
                key_points=[],
                sentiment="unknown"
            )
    
    def _fallback_importance_analysis(self, email: Email) -> ImportanceScore:
        """Fallback importance analysis using ULTRA aggressive pattern recognition."""
        score = 2.0  # Start with low score, only boost for important emails
        reasons = ["Fallback analysis"]
        safety_override = False
        category = "other"
        
        # Extract sender domain and clean sender
        sender_lower = email.sender.lower()
        if '@' in sender_lower:
            domain = sender_lower.split('@')[-1].split('>')[0]
        else:
            domain = sender_lower
        
        # Aggressive sender pattern recognition
        marketing_patterns = [
            'noreply', 'no-reply', 'donotreply', 'marketing', 'promo', 'newsletter',
            'notifications', 'deals', 'offers', 'sales', 'support'
        ]
        
        marketing_domains = [
            'mailchimp.com', 'constantcontact.com', 'campaignmonitor.com',
            'hubspot.com', 'salesforce.com', 'marketo.com', 'pardot.com',
            'mailgun.com', 'sendgrid.net', 'amazon.com', 'amazonses.com',
            'newsletters', 'email-', '-email', 'mail-', '-mail',
            'bounce', 'campaigns', 'marketing'
        ]
        
        # Check for marketing patterns in sender
        for pattern in marketing_patterns:
            if pattern in sender_lower:
                score = 1.5
                reasons = ["Marketing sender pattern", f"Contains '{pattern}'"]
                category = "promotional"
                break
        
        # Check for marketing domains
        for market_domain in marketing_domains:
            if market_domain in domain:
                score = 1.5
                reasons = ["Marketing domain", f"From {market_domain} service"]
                category = "promotional"
                break
        
        # Subject line aggressive analysis
        subject_lower = email.subject.lower()
        text = f"{email.subject} {email.text_body}".lower()
        
        # Aggressive marketing keywords (score 1-2)
        aggressive_marketing = [
            'sale', 'deal', 'offer', 'discount', 'coupon', 'promo', 'free shipping',
            'limited time', 'expires', 'save', 'shop now', 'buy now', 'order now',
            'new arrival', 'clearance', 'special offer', 'exclusive', 'member',
            'newsletter', 'update', 'notification from', 'unsubscribe', 'fitness',
            'gym', 'workout', 'membership', 'entertainment', 'concert', 'event',
            'webinar', 'conference', 'seminar', 'survey', 'feedback', 'review',
            'social media', 'follow us', 'like us', 'connect with'
        ]
        
        for keyword in aggressive_marketing:
            if keyword in text:
                if score > 2:  # Only lower if not already low
                    score = 1.8
                reasons.append(f"Marketing keyword: '{keyword}'")
                if any(cat in keyword for cat in ['newsletter', 'update', 'notification']):
                    category = "newsletter"
                elif any(cat in keyword for cat in ['social', 'follow', 'like', 'connect']):
                    category = "social"
                else:
                    category = "promotional"
                break
        
        # Safety keywords (override aggressive scoring)
        safety_keywords = ['security', 'password', 'account', 'bank', 'payment', 'verification', 'login', '2fa', 'verify']
        if any(keyword in text for keyword in safety_keywords):
            score = 9.0
            safety_override = True
            category = "security"
            reasons = ["Security-related content"]
        
        # Medical keywords (override aggressive scoring)
        medical_keywords = ['doctor', 'hospital', 'medical', 'health', 'test results', 'appointment', 'lab', 'clinic', 'patient']
        if any(keyword in text for keyword in medical_keywords):
            score = 8.5
            safety_override = True
            category = "medical"
            reasons = ["Medical communication"]
        
        # Financial keywords
        financial_keywords = ['invoice', 'payment', 'billing', 'transaction', 'transfer', 'balance']
        if any(keyword in text for keyword in financial_keywords):
            score = 8.0
            category = "financial"
            reasons = ["Financial communication"]
        
        # Personal communication indicators
        if not any(pattern in sender_lower for pattern in marketing_patterns):
            # If sender looks personal and no marketing indicators
            if '@gmail.com' in sender_lower or '@outlook.com' in sender_lower or '@yahoo.com' in sender_lower:
                if score < 6:  # Don't override financial/security
                    score = 6.0
                    category = "personal"
                    reasons.append("Personal email domain")
        
        # Automated service notifications
        automated_keywords = ['automated', 'notification', 'reminder', 'alert', 'status']
        if any(keyword in text for keyword in automated_keywords) and category == "other":
            score = 3.5
            category = "automated"
            reasons.append("Automated service notification")
        
        # Determine level based on score
        if safety_override or score >= 9:
            level = ImportanceLevel.CRITICAL
        elif score >= 7:
            level = ImportanceLevel.HIGH
        elif score >= 5:
            level = ImportanceLevel.MEDIUM
        elif score >= 2:
            level = ImportanceLevel.LOW
        else:
            level = ImportanceLevel.SPAM
        
        return ImportanceScore(
            score=score,
            level=level,
            safe_to_delete=(score < 4 and not safety_override),
            safety_override=safety_override,
            reasons=reasons,
            category=category
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()