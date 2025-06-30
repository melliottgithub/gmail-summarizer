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

4. **Set up Gmail API credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials file as `config/credentials.json`

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

## 📞 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/gmail-summarizer/issues) on GitHub.

## 🙏 Acknowledgments

- [Google Gmail API](https://developers.google.com/gmail/api) for email access
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Click](https://click.palletsprojects.com/) for CLI framework
- [OpenAI](https://openai.com/) and [Anthropic](https://www.anthropic.com/) for AI capabilities

---

**Made with ❤️ for productivity and email management**
