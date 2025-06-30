# Gmail Summarizer MVP

A tool to retrieve Gmail emails and summarize relevant content using AI.

## Features (MVP)

- 🔐 Secure Gmail API authentication
- 📧 Retrieve emails from specified time periods
- 🔍 Filter emails by relevance criteria
- 📝 AI-powered email summarization
- 💾 Store and manage email data locally
- 📊 Basic reporting and insights

## Project Structure

```
gmail-summarizer/
├── src/
│   ├── __init__.py
│   ├── gmail_client.py      # Gmail API integration
│   ├── email_processor.py   # Email filtering and processing
│   ├── summarizer.py        # AI summarization logic
│   └── storage.py           # Data storage and retrieval
├── config/
│   ├── settings.py          # Configuration management
│   └── credentials.json     # Gmail API credentials (gitignored)
├── data/                    # Local email storage
├── tests/
│   ├── __init__.py
│   ├── test_gmail_client.py
│   ├── test_email_processor.py
│   └── test_summarizer.py
├── requirements.txt
├── .env.example
├── .gitignore
└── main.py                  # CLI entry point
```

## Quick Start

1. **Setup Python environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Configure Gmail API:**
   - Enable Gmail API in Google Cloud Console
   - Download credentials.json to config/
   - Run initial authentication

3. **Run the tool:**
   ```bash
   python main.py --days 7 --summarize
   ```

## Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create credentials (OAuth 2.0 Client ID)
5. Download credentials.json and place in config/

## Configuration

Copy `.env.example` to `.env` and configure:
- AI service settings (OpenAI, Anthropic, etc.)
- Email filtering criteria
- Storage preferences

## Future Enhancements

- Web interface for email management
- Advanced AI models for better summarization
- Email categorization and tagging
- Scheduled email processing
- Integration with calendar and tasks
- Export to various formats (PDF, CSV, etc.)

## Tech Stack

- **Python 3.9+** - Core language
- **Google Gmail API** - Email retrieval
- **OpenAI/Anthropic API** - AI summarization
- **SQLite** - Local data storage
- **Click** - CLI interface
- **pytest** - Testing framework
