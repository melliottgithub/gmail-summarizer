# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gmail Summarizer is a Python CLI tool for fetching, analyzing, and managing unread Gmail emails using AI-powered importance scoring. The tool helps users identify and clean up trash emails while preserving important communications.

## Core Commands

### Development Workflow
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py <command>

# Testing
python -m pytest tests/

# Check for import issues
python -c "import src.gmail_client; print('Imports OK')"
```

### Application Commands
```bash
# Initial setup (run once)
python main.py setup

# Fetch unread emails 
python main.py unread --max-emails 50

# Analyze emails with AI
python main.py analyze --batch-size 10

# Interactive analysis
python main.py analyze -i

# View deletion candidates  
python main.py candidates --min-score 3.0

# Mark trash as read (preview)
python main.py mark-read --dry-run

# Mark trash as read (actual)
python main.py mark-read --confirm

# Full automated workflow
python main.py auto --dry-run -i
```

## Architecture

The project follows Domain-Driven Design (DDD) principles with clear separation of concerns:

### Domain Layer (`src/domain/`)
- **models.py**: Core entities (`Email`, `ImportanceScore`, `EmailSummary`) and value objects
- **services.py**: Domain services for email importance analysis business logic
- Key patterns: Entities have business methods (`is_safe_to_delete()`, `is_high_priority()`)

### Application Layer (`src/application/`)
- **email_service.py**: Orchestrates workflows, coordinates between domain and infrastructure
- Main orchestrator that handles fetch → analyze → mark-read workflows
- Manages progress callbacks and batch processing

### Infrastructure Layer (`src/infrastructure/`)
- **json_repository.py**: JSON-based email persistence with metadata tracking
- **llm_service.py**: Ollama LLM integration for AI analysis
- Repository pattern for data access, external service adapters

### Gmail Integration
- **gmail_client.py**: Gmail API client handling authentication and email fetching
- OAuth2 flow with token management
- Handles Gmail API rate limiting and error handling

## Key Dependencies

- **Ollama**: Local LLM for email analysis (requires `qwen2.5-coder:32b` model)
- **Google APIs**: Gmail API client with OAuth2 authentication  
- **Rich**: Terminal UI with progress bars and tables
- **Click**: CLI framework with command groups
- **httpx**: Async HTTP client for LLM API calls

## Configuration

### Environment Setup
- Gmail credentials: `config/credentials.json` (OAuth2 client secrets)
- OAuth tokens: `config/token.json` (auto-generated)
- Settings: `config/settings.py` handles environment variables
- Email database: `data/emails.json` (auto-created)

### Analysis Configuration
The `AnalysisConfig` class in `domain/models.py` controls:
- LLM model selection (`qwen2.5-coder:32b`)
- Batch processing size (default: 10)
- Importance thresholds for deletion candidates (default: -5.0, very aggressive)
- Safety overrides for critical emails
- Email categorization system (promotional, newsletter, social, etc.)

### Email Processing Features
- **Aggressive Scoring**: Default threshold of -5.0 marks most promotional emails for deletion
- **Pattern Recognition**: Automatic detection of marketing domains and sender patterns
- **Categorized Summaries**: After marking emails as read, shows breakdown by category
- **Category Preview**: Shows what types of emails will be deleted before action
- **Safety Overrides**: Never deletes security, financial, or medical emails

## Data Flow

1. **Fetch**: Gmail API → Domain Email objects → JSON repository
2. **Analyze**: Repository → LLM Service → Updated email scores → Repository  
3. **Mark**: Repository candidates → Gmail API modify → Progress tracking

The repository maintains analysis state between sessions, allowing incremental processing of large email batches.

## Testing Strategy

- Unit tests in `tests/` directory
- Test main CLI interface with `test_main.py`
- Mock external dependencies (Gmail API, Ollama) for reliable testing
- Test domain business logic independently

## Error Handling

- Gmail API errors: Graceful degradation with user-friendly messages
- LLM service errors: Individual email failures don't stop batch processing
- Authentication errors: Clear setup instructions in error messages
- Repository errors: Backup data before destructive operations

## Performance Considerations

- Batch processing for LLM analysis (configurable size)
- Progress callbacks for long-running operations
- Async/await for I/O bound operations (LLM calls)
- Gmail API rate limiting handled transparently
- JSON repository optimized for incremental updates