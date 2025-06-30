#!/usr/bin/env python3
"""
Gmail Summarizer MVP - Main CLI Entry Point
"""

import click
from rich.console import Console
from rich.table import Table
from datetime import datetime, timedelta
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gmail_client import GmailClient
from email_processor import EmailProcessor
from summarizer import EmailSummarizer
from storage import EmailStorage
from config.settings import Settings

console = Console()

@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """Gmail Summarizer - Retrieve and summarize your Gmail emails."""
    ctx.ensure_object(dict)
    ctx.obj['settings'] = Settings(config)

@cli.command()
@click.option('--days', '-d', default=7, help='Number of days back to retrieve emails')
@click.option('--max-emails', '-m', default=100, help='Maximum number of emails to retrieve')
@click.option('--query', '-q', help='Gmail search query')
@click.pass_context
def fetch(ctx, days, max_emails, query):
    """Fetch emails from Gmail."""
    settings = ctx.obj['settings']
    
    console.print(f"[bold blue]Fetching emails from the last {days} days...[/bold blue]")
    
    try:
        # Initialize components
        gmail_client = GmailClient(settings)
        processor = EmailProcessor(settings)
        storage = EmailStorage(settings)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch emails
        emails = gmail_client.fetch_emails(
            start_date=start_date,
            end_date=end_date,
            max_results=max_emails,
            query=query
        )
        
        console.print(f"[green]Retrieved {len(emails)} emails[/green]")
        
        # Process and filter emails
        filtered_emails = processor.filter_emails(emails)
        console.print(f"[green]Filtered to {len(filtered_emails)} relevant emails[/green]")
        
        # Store emails
        storage.store_emails(filtered_emails)
        console.print("[green]Emails stored successfully[/green]")
        
    except Exception as e:
        console.print(f"[red]Error fetching emails: {e}[/red]")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--days', '-d', default=7, help='Number of days back to summarize')
@click.option('--style', '-s', default='bullet_points', 
              type=click.Choice(['paragraph', 'bullet_points', 'keywords']),
              help='Summary style')
@click.pass_context
def summarize(ctx, days, style):
    """Summarize stored emails."""
    settings = ctx.obj['settings']
    
    console.print(f"[bold blue]Summarizing emails from the last {days} days...[/bold blue]")
    
    try:
        # Initialize components
        storage = EmailStorage(settings)
        summarizer = EmailSummarizer(settings)
        
        # Get emails from storage
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        emails = storage.get_emails(start_date, end_date)
        
        if not emails:
            console.print("[yellow]No emails found in the specified date range[/yellow]")
            return
        
        console.print(f"[green]Found {len(emails)} emails to summarize[/green]")
        
        # Generate summary
        summary = summarizer.summarize_emails(emails, style=style)
        
        # Display summary
        console.print("\n[bold green]Email Summary[/bold green]")
        console.print("=" * 50)
        console.print(summary)
        
        # Store summary
        storage.store_summary(summary, start_date, end_date, style)
        console.print("\n[green]Summary saved to database[/green]")
        
    except Exception as e:
        console.print(f"[red]Error summarizing emails: {e}[/red]")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--days', '-d', default=7, help='Number of days back to show')
@click.pass_context
def list(ctx, days):
    """List stored emails."""
    settings = ctx.obj['settings']
    
    try:
        storage = EmailStorage(settings)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        emails = storage.get_emails(start_date, end_date)
        
        if not emails:
            console.print("[yellow]No emails found in the specified date range[/yellow]")
            return
        
        # Create table
        table = Table(title=f"Emails from the last {days} days")
        table.add_column("Date", style="cyan")
        table.add_column("From", style="magenta")
        table.add_column("Subject", style="white", max_width=50)
        table.add_column("Labels", style="green")
        
        for email in emails[:20]:  # Show first 20 emails
            table.add_row(
                email.get('date', 'Unknown')[:10],
                email.get('sender', 'Unknown')[:30],
                email.get('subject', 'No Subject')[:50],
                ', '.join(email.get('labels', []))[:20]
            )
        
        console.print(table)
        
        if len(emails) > 20:
            console.print(f"[yellow]Showing first 20 of {len(emails)} emails[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error listing emails: {e}[/red]")
        raise click.ClickException(str(e))

@cli.command()
@click.pass_context
def setup(ctx):
    """Initial setup and authentication."""
    settings = ctx.obj['settings']
    
    console.print("[bold blue]Setting up Gmail Summarizer...[/bold blue]")
    
    try:
        gmail_client = GmailClient(settings)
        
        # Test authentication
        user_info = gmail_client.get_user_info()
        console.print(f"[green]Successfully authenticated as: {user_info.get('emailAddress')}[/green]")
        
        # Initialize database
        storage = EmailStorage(settings)
        storage.initialize()
        console.print("[green]Database initialized[/green]")
        
        console.print("[green]Setup complete![/green]")
        console.print("\nNext steps:")
        console.print("1. Run 'python main.py fetch' to retrieve emails")
        console.print("2. Run 'python main.py summarize' to generate summaries")
        
    except Exception as e:
        console.print(f"[red]Setup failed: {e}[/red]")
        console.print("\nPlease check:")
        console.print("1. Gmail API credentials are in config/credentials.json")
        console.print("2. AI API keys are set in .env file")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--days', '-d', default=7, help='Fetch and summarize emails from the last N days')
@click.option('--style', '-s', default='bullet_points', 
              type=click.Choice(['paragraph', 'bullet_points', 'keywords']),
              help='Summary style')
@click.pass_context
def run(ctx, days, style):
    """Fetch emails and generate summary in one command."""
    console.print("[bold blue]Running full email fetch and summarization...[/bold blue]")
    
    # Fetch emails
    ctx.invoke(fetch, days=days)
    
    # Generate summary
    ctx.invoke(summarize, days=days, style=style)

if __name__ == '__main__':
    cli()
