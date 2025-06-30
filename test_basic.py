#!/usr/bin/env python3
"""
Basic test to verify Gmail Summarizer core functionality
"""

import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_functionality():
    """Test basic functionality without requiring actual Gmail credentials."""
    
    print("🧪 Testing Gmail Summarizer core functionality...")
    
    try:
        # Test 1: Configuration loading
        print("\n1. Testing configuration...")
        from config.settings import Settings
        
        # Create minimal config for testing
        os.environ['GMAIL_CREDENTIALS_PATH'] = 'test_credentials.json'
        os.environ['OPENAI_API_KEY'] = 'test_key'
        
        # Create dummy credentials file
        import json
        with open('test_credentials.json', 'w') as f:
            json.dump({"test": "credentials"}, f)
        
        try:
            settings = Settings()
            print("   ✅ Settings loaded successfully")
        except ValueError as e:
            if "Gmail credentials file not found" in str(e):
                print("   ⚠️ Settings validation requires real credentials file")
            else:
                raise
        
        # Test 2: Email processor
        print("\n2. Testing email processor...")
        from email_processor import EmailProcessor
        
        # Create test settings object
        class TestSettings:
            exclude_senders = ['noreply@', 'no-reply@']
            exclude_subjects = ['unsubscribe', 'newsletter']
            include_only_labels = ['INBOX']
            relevance_threshold = 0.7
        
        processor = EmailProcessor(TestSettings())
        
        # Test with sample emails
        test_emails = [
            {
                'id': '1',
                'sender': 'john@example.com',
                'subject': 'Important meeting tomorrow',
                'text_body': 'Hi, we need to discuss the project status in tomorrow\'s meeting.',
                'labels': ['INBOX', 'IMPORTANT'],
                'date': datetime.now().isoformat()
            },
            {
                'id': '2',
                'sender': 'noreply@spam.com',
                'subject': 'Newsletter - Weekly updates',
                'text_body': 'This is an automated newsletter',
                'labels': ['INBOX'],
                'date': datetime.now().isoformat()
            }
        ]
        
        filtered_emails = processor.filter_emails(test_emails)
        print(f"   ✅ Filtered {len(test_emails)} emails down to {len(filtered_emails)} relevant emails")
        
        # Test 3: Email storage
        print("\n3. Testing email storage...")
        from storage import EmailStorage
        
        class TestStorageSettings:
            database_path = 'data/test_emails.db'
        
        storage = EmailStorage(TestStorageSettings())
        
        # Store test emails
        stored_count = storage.store_emails(filtered_emails)
        print(f"   ✅ Stored {stored_count} emails in database")
        
        # Retrieve emails
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        retrieved_emails = storage.get_emails(start_date, end_date)
        print(f"   ✅ Retrieved {len(retrieved_emails)} emails from database")
        
        # Test 4: Email summarizer
        print("\n4. Testing email summarizer...")
        from summarizer import EmailSummarizer
        
        class TestSummarizerSettings:
            def get_ai_config(self):
                return {}
        
        summarizer = EmailSummarizer(TestSummarizerSettings())
        
        # Generate summary
        if retrieved_emails:
            summary = summarizer.summarize_emails(retrieved_emails, style='bullet_points')
            print(f"   ✅ Generated summary ({len(summary)} characters)")
            print(f"   📝 Sample summary:\n{summary[:200]}...")
        else:
            print("   ⚠️ No emails available for summarization test")
        
        # Test 5: CLI structure
        print("\n5. Testing CLI structure...")
        
        # Import main to check CLI structure
        import main
        print("   ✅ CLI module imported successfully")
        
        print("\n🎉 All basic tests passed!")
        
        # Cleanup
        cleanup_test_files()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        cleanup_test_files()
        return False

def cleanup_test_files():
    """Clean up test files."""
    test_files = ['test_credentials.json', 'data/test_emails.db']
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception:
            pass

if __name__ == '__main__':
    print("Gmail Summarizer MVP - Basic Functionality Test")
    print("=" * 50)
    
    success = test_basic_functionality()
    
    if success:
        print("\n✅ Basic functionality test completed successfully!")
        print("\nNext steps:")
        print("1. Set up Gmail API credentials in config/credentials.json")
        print("2. Configure AI API keys in .env file")
        print("3. Run 'python main.py setup' to complete setup")
        print("4. Use 'python main.py --help' to see all available commands")
    else:
        print("\n❌ Basic functionality test failed!")
        print("Please check the error messages above and fix any issues.")
    
    exit(0 if success else 1)
