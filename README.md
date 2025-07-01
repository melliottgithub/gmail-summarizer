# Gmail Summarizer

A powerful Python CLI tool for fetching, analyzing, and summarizing unread Gmail emails. Built with modern Python libraries and designed for productivity.

## ✨ Features

- 📧 **Unread Email Fetching**: Quickly view all unread emails with a clean, organized table display
- 🎨 **Rich CLI Interface**: Beautiful terminal output with colors and formatting using Rich
- 🧠 **AI-Powered Email Analysis**: Advanced importance scoring using local LLM models (Ollama)
- 🗑️ **Smart Deletion Recommendations**: AI identifies emails safe to delete with safety overrides
- 📊 **Email Analytics**: Get insights about your unread emails including top senders and importance distribution
- 🔐 **Secure Authentication**: OAuth2 integration with Gmail API
- 🏗️ **Domain-Driven Design**: Clean architecture following DDD principles
- ⚡ **Fast & Lightweight**: Efficient email processing with minimal resource usage

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Gmail account with API access
- Google Cloud Project with Gmail API enabled
- **[Ollama](https://ollama.ai/) - Required for AI analysis features**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/melliottgithub/gmail-summarizer.git
   cd gmail-summarizer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and setup Ollama (Required for AI features)**
   
   **Step 4a: Install Ollama**
   - Go to [ollama.ai](https://ollama.ai/) and download for your OS
   - Or install via command line:
     ```bash
     # macOS/Linux
     curl -fsSL https://ollama.ai/install.sh | sh
     
     # Windows: Download from website
     ```
   
   **Step 4b: Download required models**
   ```bash
   # Download the model used for email analysis (this may take a few minutes)
   ollama pull qwen2.5-coder:32b
   
   # Verify Ollama is running
   ollama list
   ```
   
   **Step 4c: Test Ollama**
   ```bash
   # Test that Ollama is working
   ollama run qwen2.5-coder:32b "Hello, are you working?"
   ```
   
   **Note**: The AI analysis commands (`analyze`, `candidates`, `auto`) require Ollama to be running. Without Ollama, you can still use the `unread` command to fetch emails.

5. **Set up Gmail API credentials (Critical Step!)**
   
   **⚠️ Important**: This app is in development mode, so you must add your Gmail account as a test user.
   
   **Step 5a: Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "Select a project" → "New Project"
   - Name your project (e.g., "Gmail Summarizer")
   - Click "Create" and wait for project creation
   - Make sure your new project is selected in the top dropdown
   
   **Step 5b: Enable Gmail API**
   - In the left sidebar, click "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click on "Gmail API" from the results
   - Click the blue "Enable" button
   - Wait for the API to be enabled
   
   **Step 5c: Configure OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" user type (unless you have Google Workspace)
   - Fill in required fields:
     - App name: "Gmail Summarizer"
     - User support email: Your Gmail address
     - Developer contact: Your Gmail address
   - Click "Save and Continue"
   - Skip "Scopes" step (click "Save and Continue")
   - **IMPORTANT - Add Test Users:**
     - In "Test users" section, click "+ Add Users"
     - Add the Gmail account you want to use with this app
     - Click "Save" then "Save and Continue"
   - Review and click "Back to Dashboard"
   
   **Step 5d: Create OAuth Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "+ Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Name it "Gmail Summarizer Desktop"
   - Click "Create"
   
   **Step 5e: Download and Install Credentials**
   - Click the download icon (⬇️) next to your newly created credential
   - Save the JSON file
   - Rename and move it to your project:
     ```bash
     # On Windows (PowerShell)
     mkdir config -ErrorAction SilentlyContinue
     Move-Item "$env:USERPROFILE\Downloads\client_secret_*.json" "config\credentials.json"
     
     # On macOS/Linux
     mkdir -p config
     mv ~/Downloads/client_secret_*.json config/credentials.json
     ```

6. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### First Run

1. **Run initial setup**
   ```bash
   python main.py setup
   ```
   This will guide you through the OAuth flow and create necessary token files.

2. **Fetch unread emails**
   ```bash
   python main.py unread
   ```

## 📋 Commands

The Gmail Summarizer provides a comprehensive set of commands for email management, from basic fetching to advanced AI-powered cleanup workflows.

### 🚀 Quick Start Commands

**For beginners - try these first:**
```bash
# Setup authentication (run once)
python main.py setup

# Get unread emails 
python main.py unread

# Interactive AI analysis
python main.py analyze -i

# Full automatic cleanup (preview mode)
python main.py auto --dry-run -i
```

---

### 📧 `unread` - Fetch Unread Emails

Fetches fresh unread emails from Gmail and replaces the local database.

```bash
python main.py unread [OPTIONS]
```

**Options:**
- `-m, --max-emails INTEGER`: Maximum number of unread emails to fetch (default: 50)

**Examples:**
```bash
# Fetch up to 50 unread emails (default)
python main.py unread

# Fetch specific number of emails
python main.py unread --max-emails 25

# Fetch maximum emails
python main.py unread --max-emails 100
```

**What it does:**
- 📧 Fetches current unread emails from Gmail
- 🔄 Replaces database with fresh batch (clean slate each time)
- 📊 Shows email table with date, sender, subject
- 🔗 Preserves any existing analysis for emails that are still unread
- 💾 Saves emails to local JSON database

---

### 🤖 `analyze` - AI Email Analysis

Analyzes saved emails using AI to score importance and identify trash emails.

```bash
python main.py analyze [OPTIONS]
```

**Options:**
- `-b, --batch-size INTEGER`: Number of emails to analyze per batch (default: 10)
  - `1`: Slower but shows each email being analyzed
  - `10`: Faster, processes multiple emails together
- `--with-summary`: Include email summarization (slower)
- `-i, --interactive`: Interactive mode with explanations

**Examples:**
```bash
# Basic analysis
python main.py analyze

# Interactive analysis with explanations
python main.py analyze -i

# Detailed view (see each email individually)
python main.py analyze --batch-size 1

# With email summaries
python main.py analyze --with-summary
```

**AI Analysis Features:**
- 🎯 **Importance Scoring**: Each email gets a 1-10 importance score
- 🏷️ **Smart Categories**: CRITICAL, HIGH, MEDIUM, LOW, SPAM
- 🛡️ **Safety Overrides**: Never marks security/financial/medical emails as deletable
- 📊 **Progress Tracking**: Live progress with email-by-email updates (batch size 1)
- 🎨 **Color-coded Status**: Different colors for analyzing, saving, completed, error

**Interactive Mode:**
- ❓ Explains what AI analysis does
- ⚙️ Lets you choose batch size (1 for detailed view)
- 📈 Shows real-time progress with individual email details

---

### 🗑️ `candidates` - View Deletion Candidates

Shows emails that AI recommends for marking as read (trash emails).

```bash
python main.py candidates [OPTIONS]
```

**Options:**
- `--min-score FLOAT`: Minimum importance score for candidates (default: -2.0)
  - Lower values = more aggressive deletion
  - Higher values = more conservative deletion
- `-l, --limit INTEGER`: Maximum number of candidates to show (default: 20)
- `-i, --interactive`: Interactive mode with min-score explanation

**Examples:**
```bash
# Show deletion candidates
python main.py candidates

# Interactive mode (explains min-score)
python main.py candidates -i

# More aggressive deletion
python main.py candidates --min-score -5.0

# More conservative deletion  
python main.py candidates --min-score 2.0

# Show more candidates
python main.py candidates --limit 50
```

**Min-Score Guidelines:**
- `3.0`: **ULTRA AGGRESSIVE** (ruthlessly deletes ALL promotional content) - **NEW DEFAULT**
- `4.0`: **Very aggressive** (deletes most trash)
- `5.0`: **Aggressive** (deletes clear trash)
- `6.0`: **Moderate** (conservative approach)
- `7.0`: **Conservative** (deletes only obvious spam)
- `8.0`: **Very conservative** (deletes almost nothing)

**What it shows:**
- 📋 Table of emails recommended for deletion
- 📊 Score, importance level, and reasons for each email
- 📈 Statistics by importance level
- 💾 Estimated space savings

---

### ✅ `mark-read` - Mark Trash as Read

Marks trash emails as read in Gmail to clean up your unread count.

```bash
python main.py mark-read [OPTIONS]
```

**Options:**
- `--dry-run`: Preview which emails will be marked as read (safe)
- `--confirm`: Actually mark emails as read in Gmail
- `--min-score FLOAT`: Minimum score threshold (default: -5.0, very aggressive)
- `-i, --interactive`: Interactive mode with explanations

**Examples:**
```bash
# Preview what will be marked as read
python main.py mark-read --dry-run

# Actually mark emails as read
python main.py mark-read --confirm

# Interactive mode (explains everything)
python main.py mark-read -i

# More aggressive marking
python main.py mark-read --confirm --min-score -5.0
```

**Safety Features:**
- 🛡️ **Safe Operation**: Emails are marked as read, not deleted
- 🔄 **Reversible**: You can always mark emails as unread again
- 👀 **Preview Mode**: Always preview with `--dry-run` first
- ⚠️ **Confirmation Required**: Must use `--confirm` to actually make changes

**Interactive Mode:**
- ❓ Explains what marking as read does
- ⚙️ Helps you choose between preview and confirm mode
- 📊 Shows impact on unread count

---

### 🚀 `auto` - Complete Workflow

Runs the entire email cleanup workflow automatically: fetch → analyze → mark-read.

```bash
python main.py auto [OPTIONS]
```

**Options:**
- `-m, --max-emails INTEGER`: Maximum emails to fetch (default: 50)
- `--min-score FLOAT`: Score threshold for marking as read (default: -5.0, very aggressive)
- `--dry-run`: Preview entire workflow without making changes
- `-i, --interactive`: Interactive mode with explanations and confirmations

**Examples:**
```bash
# Full workflow preview (safe)
python main.py auto --dry-run

# Interactive preview with explanations
python main.py auto --dry-run -i

# Actually run full workflow
python main.py auto

# Interactive full workflow
python main.py auto -i

# Custom settings
python main.py auto --max-emails 100 --min-score -3.0
```

**Workflow Steps:**
1. 📧 **Fetch**: Gets unread emails from Gmail
2. 🤖 **Analyze**: AI scores all emails for importance
3. 🗑️ **Identify**: Finds emails safe to mark as read
4. ✅ **Execute**: Marks trash emails as read (or shows preview)

**Interactive Mode:**
- 📋 Explains the complete workflow
- ⚙️ Shows all settings before starting
- ❓ Asks for confirmation at each major step
- 📊 Provides detailed progress and final summary

---

### ⚙️ `setup` - Initial Setup

Initial setup and authentication with Gmail API.

```bash
python main.py setup
```

**What it does:**
- 🔐 Sets up OAuth2 authentication with Gmail
- 📧 Tests Gmail API access
- 💾 Creates necessary token files
- ✅ Verifies everything is working

**Run this once after installation to get started.**

---

## 🔄 Typical Workflows

### Daily Email Cleanup
```bash
# Quick cleanup (recommended)
python main.py auto --dry-run -i     # Preview with explanations
python main.py auto -i               # Actually clean up

# Or step by step
python main.py unread                # See what's unread
python main.py analyze -i            # Analyze with AI
python main.py candidates -i         # Review deletion candidates
python main.py mark-read --confirm   # Clean up
```

### First Time Setup
```bash
python main.py setup                 # Authenticate with Gmail
python main.py unread                # Get your unread emails
python main.py analyze -i            # Try AI analysis (interactive)
python main.py candidates -i         # See what can be cleaned up
python main.py mark-read --dry-run   # Preview cleanup
python main.py mark-read --confirm   # Actually clean up
```

### Batch Processing
```bash
# Process lots of emails efficiently
python main.py unread --max-emails 200
python main.py analyze --batch-size 10
python main.py mark-read --confirm --min-score -1.0
```

### Individual Review
```bash
# See each email being analyzed
python main.py unread --max-emails 20
python main.py analyze --batch-size 1
python main.py candidates --limit 50
```

## 📦 Dependencies

- **google-api-python-client** - Gmail API access
- **google-auth** & **google-auth-oauthlib** - Secure OAuth2 authentication
- **click** - Modern CLI framework
- **rich** - Beautiful terminal output with colors and tables
- **python-dotenv** - Environment variable management
- **httpx** - Modern HTTP client for LLM API calls

**AI Analysis**: Uses Ollama with `qwen2.5-coder:32b` model for local AI processing

## 🏗️ Project Structure

```
gmail-summarizer/
├── main.py                     # Main CLI application
├── src/                        # Source code
│   ├── __init__.py
│   ├── gmail_client.py         # Gmail API client
│   ├── domain/                 # Domain layer (DDD)
│   │   ├── __init__.py
│   │   ├── models.py           # Domain models and value objects
│   │   └── services.py         # Domain services
│   ├── infrastructure/         # Infrastructure layer
│   │   ├── __init__.py
│   │   ├── json_repository.py  # JSON email storage
│   │   └── llm_service.py      # LLM integration (Ollama)
│   └── application/            # Application layer
│       ├── __init__.py
│       └── email_service.py    # Application services
├── config/                     # Configuration files
│   ├── settings.py             # Settings management
│   ├── credentials.json        # Gmail API credentials (not in repo)
│   └── token.json             # OAuth tokens (not in repo)
├── data/                       # Email database (created automatically)
│   └── emails.json            # Local email storage (not in repo)
├── requirements.txt            # Python dependencies
├── .env                       # Environment variables (not in repo)
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🔧 Troubleshooting

### Common Issues

**Problem**: "Access blocked: This app's request is invalid"
- **Solution**: Make sure you added your Gmail account as a test user in the OAuth consent screen (Step 4c above)

**Problem**: "The file config/credentials.json was not found"
- **Solution**: Download the credentials file from Google Cloud Console and place it in the `config/` directory
- Make sure the file is named exactly `credentials.json`

**Problem**: "This app isn't verified"
- **Solution**: Click "Advanced" → "Go to Gmail Summarizer (unsafe)" - this is normal for development apps

**Problem**: "insufficient authentication scopes"
- **Solution**: Delete `config/token.json` and run `python main.py setup` again to re-authenticate

**Problem**: No unread emails showing but you have unread emails
- **Solution**: Check if your Gmail account has unread emails. The app only shows emails marked as "unread" in Gmail

**Problem**: "Connection refused" or "Ollama not responding" when using analyze/auto commands
- **Solution**: Make sure Ollama is running. Run `ollama serve` in a terminal, or restart the Ollama app
- Check if the model is downloaded: `ollama list`
- Test Ollama: `ollama run qwen2.5-coder:32b "test"`

**Problem**: "Model not found" error during analysis
- **Solution**: Download the required model: `ollama pull qwen2.5-coder:32b`

### Getting Help

If you're still having issues:
1. Check the [Issues page](https://github.com/melliottgithub/gmail-summarizer/issues) for similar problems
2. Run with debug mode: Set `DEBUG=true` in your `.env` file
3. Create a new issue with the error message and steps you followed

## 📞 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/melliottgithub/gmail-summarizer/issues) on GitHub.

## 🙏 Acknowledgments

- [Google Gmail API](https://developers.google.com/gmail/api) for email access
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Click](https://click.palletsprojects.com/) for CLI framework
- [Ollama](https://ollama.ai/) for local AI capabilities

