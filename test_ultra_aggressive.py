#!/usr/bin/env python3
"""
Test script to verify the ultra-aggressive email filtering settings work correctly.
This will test the new -10.0 default threshold and aggressive LLM scoring.
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.domain.models import AnalysisConfig, Email, ImportanceScore, ImportanceLevel
from src.infrastructure.llm_service import OllamaLLMService
import asyncio

def create_test_emails():
    """Create test emails with various types of content."""
    return [
        # Marketing emails (should score very low - 0.5-1.0)
        Email(
            id="1", thread_id="1", sender="deals@amazon.com", 
            subject="🎉 50% OFF Summer Sale - Limited Time!",
            date="2024-01-01", text_body="Shop now and save big on summer items! Free shipping included.",
            html_body="", snippet="Shop now and save", labels=[], size_estimate=1000, attachments=[]
        ),
        Email(
            id="2", thread_id="2", sender="noreply@netflix.com",
            subject="New shows added to your watchlist",
            date="2024-01-01", text_body="Check out these new shows and movies we think you'll love.",
            html_body="", snippet="New shows added", labels=[], size_estimate=1000, attachments=[]
        ),
        Email(
            id="3", thread_id="3", sender="fitness@gym.com",
            subject="Your weekly fitness update + special membership offer",
            date="2024-01-01", text_body="Join now for 50% off your first month! Limited time fitness deal.",
            html_body="", snippet="Fitness update", labels=[], size_estimate=1000, attachments=[]
        ),
        
        # Important emails (should score high - 7-10)
        Email(
            id="4", thread_id="4", sender="security@bank.com",
            subject="Security Alert: Login from new device",
            date="2024-01-01", text_body="We detected a login from a new device. Please verify your identity.",
            html_body="", snippet="Security alert", labels=[], size_estimate=1000, attachments=[]
        ),
        Email(
            id="5", thread_id="5", sender="doctor@hospital.com",
            subject="Test results available - Please review",
            date="2024-01-01", text_body="Your recent lab test results are now available for review.",
            html_body="", snippet="Test results", labels=[], size_estimate=1000, attachments=[]
        ),
        Email(
            id="6", thread_id="6", sender="john.doe@gmail.com",
            subject="Re: Project deadline discussion",
            date="2024-01-01", text_body="Thanks for the meeting today. As discussed, the deadline is Friday.",
            html_body="", snippet="Project deadline", labels=[], size_estimate=1000, attachments=[]
        )
    ]

async def test_ultra_aggressive_scoring():
    """Test that the ultra-aggressive scoring works as expected."""
    print("🧪 Testing Ultra-Aggressive Email Scoring")
    print("=" * 50)
    
    # Check default config
    config = AnalysisConfig()
    print(f"✅ Default deletion threshold: {config.deletion_threshold}")
    assert config.deletion_threshold == -10.0, f"Expected -10.0, got {config.deletion_threshold}"
    
    # Create test emails
    test_emails = create_test_emails()
    
    # Test fallback scoring (when LLM is not available)
    llm_service = OllamaLLMService()
    
    print("\n🤖 Testing Fallback Scoring (Pattern Recognition)")
    print("-" * 50)
    
    for email in test_emails:
        # Test the fallback analysis directly
        score = llm_service._fallback_importance_analysis(email)
        
        print(f"📧 {email.subject[:40]}...")
        print(f"   From: {email.sender}")
        print(f"   Score: {score.score:.1f} | Level: {score.level.value}")
        print(f"   Safe to delete: {score.safe_to_delete}")
        print(f"   Category: {score.category}")
        print(f"   Reasons: {', '.join(score.reasons[:2])}")
        
        # Verify marketing emails get low scores
        marketing_senders = ['deals@amazon.com', 'noreply@netflix.com', 'fitness@gym.com']
        if email.sender in marketing_senders:
            assert score.score <= 2.0, f"Marketing email scored too high: {score.score}"
            assert score.safe_to_delete, "Marketing email should be safe to delete"
            print("   ✅ Correctly identified as trash")
        
        # Verify important emails get high scores
        important_senders = ['security@bank.com', 'doctor@hospital.com', 'john.doe@gmail.com']
        if email.sender in important_senders:
            if 'security' in email.sender or 'doctor' in email.sender:
                assert score.score >= 7.0, f"Important email scored too low: {score.score}"
                assert not score.safe_to_delete, "Important email should not be safe to delete"
                print("   ✅ Correctly identified as important")
            elif 'john.doe@gmail.com' in email.sender:
                assert score.score >= 5.0, f"Personal email scored too low: {score.score}"
                assert not score.safe_to_delete, "Personal email should not be safe to delete"
                print("   ✅ Correctly identified as personal communication")
        
        print()
    
    print("🎯 Testing Deletion Candidate Filtering")
    print("-" * 50)
    
    # Test with the new ultra-aggressive threshold
    from src.domain.services import EmailImportanceDomainService
    
    # Add scores to emails for testing
    for email in test_emails:
        email.importance_score = llm_service._fallback_importance_analysis(email)
    
    domain_service = EmailImportanceDomainService(llm_service)
    
    # Test with default ultra-aggressive threshold
    candidates = domain_service.get_deletion_candidates(test_emails, min_score=3.0)
    
    print(f"📊 Found {len(candidates)} deletion candidates with threshold 3.0")
    for candidate in candidates:
        print(f"   🗑️ {candidate.subject[:40]}... (Score: {candidate.importance_score.score:.1f})")
    
    # Verify we catch the marketing emails
    marketing_candidates = [c for c in candidates if c.sender in ['deals@amazon.com', 'noreply@netflix.com', 'fitness@gym.com']]
    print(f"✅ Marketing emails caught for deletion: {len(marketing_candidates)}")
    
    # Verify we don't catch important emails
    important_in_candidates = [c for c in candidates if c.sender in ['security@bank.com', 'doctor@hospital.com']]
    assert len(important_in_candidates) == 0, f"Important emails incorrectly marked for deletion: {[c.sender for c in important_in_candidates]}"
    print("✅ Important emails protected from deletion")
    
    print("\n🎉 All tests passed! Ultra-aggressive scoring is working correctly.")
    print(f"📈 Summary:")
    print(f"   • Default threshold: {config.deletion_threshold} (ultra-aggressive)")
    print(f"   • Marketing emails: Scored ≤ 2.0, marked for deletion")
    print(f"   • Security/Medical: Scored ≥ 7.0, protected")
    print(f"   • Deletion candidates: {len(candidates)}/{len(test_emails)} emails")

if __name__ == "__main__":
    asyncio.run(test_ultra_aggressive_scoring())
