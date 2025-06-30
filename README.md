# Gmail Summarizer

A powerful Python CLI tool for fetching, analyzing, and summarizing unread Gmail emails. Built with modern Python libraries and designed for productivity.

## ✨ Features

- 📧 **Unread Email Fetching**: Quickly view all unread emails with a clean, organized table display
- 🎨 **Rich CLI Interface**: Beautiful terminal output with colors and formatting using Rich
- 📊 **Email Analytics**: Get insights about your unread emails including top senders
- 🔐 **Secure Authentication**: OAuth2 integration with Gmail API
- 🤖 **AI Integration Ready**: Built-in support for OpenAI and Anthropic APIs for future summarization features
- ⚡ **Fast & Lightweight**: Efficient email processing with minimal resource usage

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Gmail account with API access
- Google Cloud Project with Gmail API enabled

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/gmail-summarizer.git
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

4. **Set up Gmail API credentials (Critical Step!)**
   
   **⚠️ Important**: This app is in development mode, so you must add your Gmail account as a test user.
   
   **Step 4a: Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "Select a project" → "New Project"
   - Name your project (e.g., "Gmail Summarizer")
   - Click "Create" and wait for project creation
   - Make sure your new project is selected in the top dropdown
   
   **Step 4b: Enable Gmail API**
   - In the left sidebar, click "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click on "Gmail API" from the results
   - Click the blue "Enable" button
   - Wait for the API to be enabled
   
   **Step 4c: Configure OAuth Consent Screen**
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
   
   **Step 4d: Create OAuth Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "+ Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Name it "Gmail Summarizer Desktop"
   - Click "Create"
   
   **Step 4e: Download and Install Credentials**
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

5. **Create environment file**
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

### `unread`
Fetch and display unread emails in a formatted table.

```bash
python main.py unread [OPTIONS]
```

**Options:**
- `-m, --max-emails INTEGER`: Maximum number of unread emails to show (default: 50)

**Example:**
```bash
python main.py unread --max-emails 25
```

### `setup`
Initial setup and authentication with Gmail API.

```bash
python main.py setup
```

## 📦 Dependencies

**Only 6 lightweight packages!**

This project uses minimal dependencies to keep installation fast and simple:

- **google-api-python-client** - Gmail API access
- **google-auth** & **google-auth-oauthlib** - Secure OAuth2 authentication
- **click** - Modern CLI framework
- **rich** - Beautiful terminal output with colors and tables
- **python-dotenv** - Environment variable management

## 🏗️ Project Structure

```
gmail-summarizer/
├── main.py                 # Main CLI application
├── src/                    # Source code
│   ├── __init__.py
│   └── gmail_client.py     # Gmail API client
├── config/                 # Configuration files
│   ├── __init__.py
│   ├── settings.py         # Settings management
│   ├── credentials.json    # Gmail API credentials (not in repo)
│   └── token.json         # OAuth tokens (not in repo)
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (not in repo)
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

The following environment variables can be set in your `.env` file:

```env
# Gmail API Configuration
GMAIL_CREDENTIALS_PATH=config/credentials.json
GMAIL_TOKEN_PATH=config/token.json

# AI Integration (Optional)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Application Settings
MAX_EMAILS_DEFAULT=50
DEBUG=false
```

### Gmail API Setup

1. **Create Google Cloud Project**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Gmail API**
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it

3. **Create Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Desktop Application"
   - Download the JSON file and save as `config/credentials.json`

## 🔮 Future Features

- 🤖 **AI Summarization**: Automatic email summarization using OpenAI/Anthropic
- 📈 **Advanced Analytics**: Email trends, sender patterns, and productivity insights
- 🏷️ **Smart Categorization**: Automatic email categorization and labeling
- 📱 **Export Options**: Export emails to various formats (CSV, JSON, PDF)
- 🔔 **Notification System**: Desktop notifications for important emails
- 📅 **Scheduling**: Automated email processing and reporting

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=src
```

## 🛠️ Development

### Code Formatting

This project uses `black` for code formatting:

```bash
black .
```

### Linting

Use `flake8` for linting:

```bash
flake8 src/ main.py
```

### Pre-commit Hooks

Set up pre-commit hooks for automatic formatting and linting:

```bash
pre-commit install
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

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

### Getting Help

If you're still having issues:
1. Check the [Issues page](https://github.com/yourusername/gmail-summarizer/issues) for similar problems
2. Run with debug mode: Set `DEBUG=true` in your `.env` file
3. Create a new issue with the error message and steps you followed

## 📞 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/gmail-summarizer/issues) on GitHub.

## 🙏 Acknowledgments

- [Google Gmail API](https://developers.google.com/gmail/api) for email access
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Click](https://click.palletsprojects.com/) for CLI framework
- [OpenAI](https://openai.com/) and [Anthropic](https://www.anthropic.com/) for AI capabilities

---

**Made with ❤️ for productivity and email management**
