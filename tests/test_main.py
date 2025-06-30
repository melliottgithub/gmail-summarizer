#!/usr/bin/env python3
"""
Test file for Gmail Summarizer main functionality.
Basic tests to ensure the CLI and core functionality work.
"""

import pytest
import click
from click.testing import CliRunner
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from main import cli


class TestCLI:
    """Test the main CLI functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test that the CLI help command works."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Gmail Unread Email Fetcher' in result.output
    
    def test_unread_command_help(self):
        """Test that the unread command help works."""
        result = self.runner.invoke(cli, ['unread', '--help'])
        assert result.exit_code == 0
        assert 'Fetch and display unread emails' in result.output
        assert '--max-emails' in result.output
    
    def test_setup_command_help(self):
        """Test that the setup command help works."""
        result = self.runner.invoke(cli, ['setup', '--help'])
        assert result.exit_code == 0
        assert 'Initial setup and authentication' in result.output


class TestProjectStructure:
    """Test that the project structure is correct."""
    
    def test_required_files_exist(self):
        """Test that all required files exist."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        required_files = [
            'main.py',
            'requirements.txt',
            'README.md',
            '.gitignore',
            'src/__init__.py',
            'src/gmail_client.py',
            'config/__init__.py',
            'config/settings.py'
        ]
        
        for file_path in required_files:
            full_path = os.path.join(base_dir, file_path)
            assert os.path.exists(full_path), f"Required file {file_path} does not exist"
    
    def test_requirements_txt_has_dependencies(self):
        """Test that requirements.txt contains expected dependencies."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        requirements_path = os.path.join(base_dir, 'requirements.txt')
        
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        expected_deps = [
            'google-api-python-client',
            'google-auth',
            'click',
            'rich',
            'python-dotenv'
        ]
        
        for dep in expected_deps:
            assert dep in content, f"Expected dependency {dep} not found in requirements.txt"
    
    def test_readme_exists_and_has_content(self):
        """Test that README.md exists and has expected content."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        readme_path = os.path.join(base_dir, 'README.md')
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        expected_sections = [
            '# Gmail Summarizer',
            '## ✨ Features',
            '## 🚀 Quick Start',
            '## 📋 Commands',
            '## 🏗️ Project Structure'
        ]
        
        for section in expected_sections:
            assert section in content, f"Expected section {section} not found in README.md"


if __name__ == '__main__':
    pytest.main([__file__])
