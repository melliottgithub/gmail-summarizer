"""
LLM-based email analysis service using Ollama.
"""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime

from domain.models import Email, ImportanceScore, EmailSummary, ImportanceLevel, AnalysisConfig
from domain.services import EmailAnalysisService

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
You are an aggressive email importance analyzer. Your job is to identify emails that are truly TRASH and safe to delete.

Email Details:
- From: {email.sender}
- Subject: {email.subject}
- Date: {email.date}
- Content: {email.text_body[:1000]}...

TRASH EMAIL CATEGORIES (mark as safe_to_delete=true, low scores):
- Marketing/promotional emails (sales, deals, newsletters)
- Fitness center promotions, gym memberships
- Entertainment promotions (Netflix, sports, events)
- Store promotions (Amazon deals, shopping)
- Social media notifications
- Travel deal alerts (unless specific bookings)
- Restaurant/food delivery promotions
- Generic job board spam

KEEP EMAILS (mark as safe_to_delete=false, high scores):
- Security alerts, password resets, account notifications
- Banking, financial, payment confirmations
- Medical communications, healthcare
- Direct personal communications
- Specific job applications you applied for
- Legal documents, contracts, taxes
- Service confirmations (actual bookings, purchases)

BE AGGRESSIVE: If it looks like marketing trash, score it 1-3 and mark safe_to_delete=true.
BE CONSERVATIVE: Only for security/financial/medical emails, use safety_override=true.

Respond in this exact JSON format:
{{
    "importance_score": <number 1-10>,
    "importance_level": "<CRITICAL|HIGH|MEDIUM|LOW|SPAM>",
    "safe_to_delete": <true/false>,
    "safety_override": <true/false>,
    "reasons": ["reason 1", "reason 2", "reason 3"]
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
                    reasons=data.get('reasons', ['LLM analysis'])
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
        """Fallback importance analysis using simple rules."""
        score = 5.0
        reasons = ["Fallback analysis"]
        safety_override = False
        
        # Basic keyword analysis
        text = f"{email.subject} {email.text_body}".lower()
        
        # Safety keywords
        safety_keywords = ['security', 'password', 'account', 'bank', 'payment', 'verification']
        if any(keyword in text for keyword in safety_keywords):
            score += 5
            safety_override = True
            reasons.append("Contains security-related keywords")
        
        # Urgency keywords
        urgent_keywords = ['urgent', 'asap', 'deadline', 'important']
        if any(keyword in text for keyword in urgent_keywords):
            score += 3
            reasons.append("Contains urgency keywords")
        
        # Marketing indicators
        marketing_keywords = ['unsubscribe', 'promotion', 'deal', 'sale']
        if any(keyword in text for keyword in marketing_keywords):
            score -= 3
            reasons.append("Appears to be marketing content")
        
        # Determine level
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
            safe_to_delete=(score < 3 and not safety_override),
            safety_override=safety_override,
            reasons=reasons
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()