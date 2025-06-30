#!/usr/bin/env python3
"""
Gmail Unread Email Fetcher - Ultra Simple
Just fetch unread emails and display them.
"""

import click
from rich.console import Console
from rich.table import Table
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gmail_client import GmailClient
from config.settings import Settings

console = Console()

@click.group()
@click.pass_context
def cli(ctx):
    """Gmail Unread Email Fetcher."""
    ctx.ensure_object(dict)
    ctx.obj['settings'] = Settings()

@cli.command()
@click.option('--max-emails', '-m', default=50, help='Maximum number of unread emails to show')
@click.pass_context
def unread(ctx, max_emails):
    """Fetch and display unread emails."""
    settings = ctx.obj['settings']
    
    console.print("[bold blue]Fetching unread emails...[/bold blue]")
    
    try:
        # Initialize Gmail client
        gmail_client = GmailClient(settings)
        
        # Fetch unread emails using Gmail query
        emails = gmail_client.fetch_emails(
            max_results=max_emails,
            query="is:unread"
        )
        
        if not emails:
            console.print("[green]🎉 No unread emails! Your inbox is clean.[/green]")
            return
        
        console.print(f"[yellow]Found {len(emails)} unread emails[/yellow]")
        
        # Create table for unread emails
        table = Table(title=f"📧 Unread Emails ({len(emails)})")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Date", style="cyan", width=12)
        table.add_column("From", style="magenta", max_width=25)
        table.add_column("Subject", style="white", max_width=50)
        
        for i, email in enumerate(emails, 1):
            # Parse date for better display
            date_str = email.get('date', 'Unknown')
            try:
                from datetime import datetime
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_display = dt.strftime('%m/%d %H:%M')
                else:
                    date_display = date_str[:10]
            except:
                date_display = date_str[:10]
            
            # Clean sender name
            sender = email.get('sender', 'Unknown')
            if '<' in sender:
                sender = sender.split('<')[0].strip()
            
            table.add_row(
                str(i),
                date_display,
                sender[:25],
                email.get('subject', 'No Subject')[:50]
            )
        
        console.print(table)
        
        # Show summary statistics
        console.print(f"\n[bold cyan]📊 Summary:[/bold cyan]")
        
        # Count by sender
        sender_counts = {}
        for email in emails:
            sender = email.get('sender', 'Unknown')
            if '<' in sender:
                sender = sender.split('<')[0].strip()
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        console.print("\n[yellow]📨 Top Senders:[/yellow]")
        for sender, count in top_senders:
            console.print(f"  • {sender[:30]}: {count} email{'s' if count > 1 else ''}")
        
    except Exception as e:
        console.print(f"[red]Error fetching unread emails: {e}[/red]")
        raise click.ClickException(str(e))

@cli.command()
@click.pass_context
def setup(ctx):
    """Initial setup and authentication."""
    settings = ctx.obj['settings']
    
    console.print("[bold blue]Setting up Gmail access...[/bold blue]")
    
    try:
        gmail_client = GmailClient(settings)
        
        # Test authentication
        user_info = gmail_client.get_user_info()
        console.print(f"[green]✅ Successfully authenticated as: {user_info.get('emailAddress')}[/green]")
        
        console.print("[green]🎉 Setup complete![/green]")
        console.print("\nNext step:")
        console.print("• Run 'python main_minimal.py unread' to see unread emails")
        
    except Exception as e:
        console.print(f"[red]❌ Setup failed: {e}[/red]")
        console.print("\nPlease check:")
        console.print("1. Gmail API credentials are in config/credentials.json")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli()
