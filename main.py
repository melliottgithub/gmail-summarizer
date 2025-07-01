#!/usr/bin/env python3
"""
Gmail Unread Email Fetcher - Ultra Simple
Just fetch unread emails and display them.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import os
import sys
import asyncio
import logging

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.gmail_client import GmailClient
from config.settings import Settings
from src.application.email_service import EmailApplicationService
from src.domain.models import AnalysisConfig

console = Console()
logger = logging.getLogger(__name__)

@click.group()
@click.pass_context
def cli(ctx):
    """Gmail Unread Email Fetcher."""
    ctx.ensure_object(dict)
    ctx.obj['settings'] = Settings()

@cli.command()
@click.option('--max-emails', '-m', default=50, help='Maximum number of unread emails to fetch')
@click.pass_context
def unread(ctx, max_emails):
    """Fetch unread emails and save to local database."""
    asyncio.run(_unread_async(ctx, max_emails))

async def _unread_async(ctx, max_emails):
    settings = ctx.obj['settings']
    
    console.print("[bold blue]Fetching unread emails...[/bold blue]")
    
    try:
        # Initialize services
        gmail_client = GmailClient(settings)
        config = AnalysisConfig()
        email_service = EmailApplicationService(gmail_client, config)
        
        # Fetch and save unread emails
        domain_emails = email_service.fetch_and_save_unread_emails(max_results=max_emails)
        
        if not domain_emails:
            console.print("[green]🎉 No unread emails! Your inbox is clean.[/green]")
            return
        
        console.print(f"[yellow]Found {len(domain_emails)} unread emails[/yellow]")
        console.print(f"[green]✅ Replaced database with fresh unread emails[/green]")
        
        # Show database metadata
        metadata = email_service.get_database_metadata()
        if metadata:
            console.print(f"[dim]Database: {metadata.get('total_emails', 0)} total emails, {metadata.get('analyzed_count', 0)} analyzed[/dim]")
        
        # Format emails for display (fresh batch, no analysis yet)
        formatted_emails = email_service.format_emails_for_display(domain_emails)
        
        # Check if we have any analyzed emails to show importance
        has_analysis = any(email['importance']['level'] != 'UNKNOWN' for email in formatted_emails)
        
        # Create table with conditional importance columns
        table = Table(title=f"📧 Unread Emails ({len(formatted_emails)}) - Fresh Batch")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Date", style="cyan", width=12)
        table.add_column("From", style="magenta", max_width=25)
        table.add_column("Subject", style="white", max_width=40)
        
        if has_analysis:
            table.add_column("Score", style="yellow", width=6)
            table.add_column("Level", style="yellow", width=8)
        
        for i, email in enumerate(formatted_emails, 1):
            row_data = [
                str(i),
                email['date'],
                email['sender'],
                email['subject']
            ]
            
            if has_analysis:
                importance = email['importance']
                if importance['level'] != 'UNKNOWN':
                    row_data.extend([
                        f"{importance['score']:.1f}",
                        f"[{importance['color']}]{importance['level']}[/{importance['color']}]"
                    ])
                else:
                    row_data.extend(['-', 'PENDING'])
            
            table.add_row(*row_data)
        
        console.print(table)
        
        # Show analysis summary if we have analyzed emails
        if has_analysis:
            analyzed_count = sum(1 for email in formatted_emails if email['importance']['level'] != 'UNKNOWN')
            pending_count = len(formatted_emails) - analyzed_count
            
            console.print(f"\n[bold cyan]🤖 AI Analysis Status:[/bold cyan]")
            console.print(f"  • Analyzed: {analyzed_count} of {len(formatted_emails)} unread emails")
            if pending_count > 0:
                console.print(f"  • Pending analysis: {pending_count} emails")
            
            # Show importance distribution
            level_counts = {}
            safe_delete_count = 0
            for email in formatted_emails:
                if email['importance']['level'] != 'UNKNOWN':
                    level = email['importance']['level']
                    level_counts[level] = level_counts.get(level, 0) + 1
                    if email['importance'].get('safe_to_delete', False):
                        safe_delete_count += 1
            
            if level_counts:
                console.print("\n[yellow]📊 Importance Distribution:[/yellow]")
                for level, count in sorted(level_counts.items()):
                    color = {
                        'CRITICAL': 'bright_red',
                        'HIGH': 'red', 
                        'MEDIUM': 'yellow',
                        'LOW': 'blue',
                        'SPAM': 'dim'
                    }.get(level, 'white')
                    console.print(f"  • [{color}]{level}[/{color}]: {count} email{'s' if count > 1 else ''}")
                
                if safe_delete_count > 0:
                    console.print(f"  • [red]Safe to mark as read: {safe_delete_count} emails[/red]")
        else:
            # Show basic statistics only if no analysis present
            console.print(f"\n[bold cyan]📊 Summary:[/bold cyan]")
            
            # Count by sender
            sender_counts = {}
            for email in formatted_emails:
                sender = email['sender']
                sender_counts[sender] = sender_counts.get(sender, 0) + 1
            
            top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            console.print("\n[yellow]📨 Top Senders:[/yellow]")
            for sender, count in top_senders:
                console.print(f"  • {sender[:30]}: {count} email{'s' if count > 1 else ''}")
        
        # Show next steps
        console.print(f"\n[bold blue]🔥 Next Steps:[/bold blue]")
        if has_analysis:
            pending_count = sum(1 for email in formatted_emails if email['importance']['level'] == 'UNKNOWN')
            if pending_count > 0:
                console.print(f"  • Run [bold]python main.py analyze -i[/bold] to analyze {pending_count} pending emails (interactive)")
            console.print("  • Run [bold]python main.py candidates -i[/bold] to see deletion recommendations (interactive)")
            console.print("  • Run [bold]python main.py mark-read --dry-run[/bold] to preview marking trash as read")
        else:
            console.print("  • Run [bold]python main.py analyze -i[/bold] to analyze importance with AI (interactive)")
            console.print("  • Run [bold]python main.py auto --dry-run -i[/bold] to run full workflow (interactive preview)")
            console.print("  • Run [bold]python main.py candidates[/bold] to see deletion recommendations")
            
        # Clean up
        await email_service.close()
        
    except Exception as e:
        console.print(f"[red]Error fetching unread emails: {e}[/red]")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--batch-size', '-b', default=10, help='Number of emails to analyze per batch (1=slower but see each email, 10=faster)')
@click.option('--with-summary', is_flag=True, help='Include email summarization (slower)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode with explanations')
@click.pass_context
def analyze(ctx, batch_size, with_summary, interactive):
    """Analyze saved emails for importance using AI."""
    asyncio.run(_analyze_async(ctx, batch_size, with_summary, interactive))

async def _analyze_async(ctx, batch_size, with_summary, interactive):
    settings = ctx.obj['settings']
    
    if interactive:
        console.print("[bold blue]🤖 AI Email Analysis Explanation[/bold blue]")
        console.print("\n[yellow]What this does:[/yellow]")
        console.print("• Uses AI to score each email's importance (1-10 scale)")
        console.print("• Identifies promotional/marketing emails as 'trash' (low scores)")
        console.print("• Marks security/financial/medical emails as 'keep' (high scores)")
        console.print("• Analyzes sender, subject, and email content")
        
        console.print(f"\n[cyan]Current batch size: {batch_size} emails at once[/cyan]")
        console.print("• Batch size 1: Slower but you see each email being analyzed")
        console.print("• Batch size 10: Faster, processes multiple emails together")
        
        if click.confirm("\n🔄 Do you want to change batch size to 1 to see individual email analysis?"):
            batch_size = 1
            console.print("[green]✅ Changed to batch size 1 for detailed view[/green]")
        
        console.print(f"\n[bold blue]🤖 Starting analysis with batch size {batch_size}...[/bold blue]")
    else:
        console.print("[bold blue]🤖 Analyzing saved emails with AI...[/bold blue]")
    
    try:
        # Initialize service without Gmail client (not needed for analysis)
        config = AnalysisConfig(
            max_batch_size=batch_size,
            enable_summarization=with_summary
        )
        email_service = EmailApplicationService(config=config)
        
        # Check if we have emails to analyze
        metadata = email_service.get_database_metadata()
        if not metadata:
            console.print("[red]❌ No email database found. Run 'python main.py unread' first.[/red]")
            return
        
        total_emails = metadata.get('total_emails', 0)
        analyzed_count = metadata.get('analyzed_count', 0)
        pending_count = total_emails - analyzed_count
        
        if pending_count == 0:
            console.print("[green]✅ All emails already analyzed![/green]")
            console.print("Run [bold]python main.py candidates[/bold] to see deletion recommendations")
            return
        
        console.print(f"[yellow]Found {pending_count} unanalyzed emails (out of {total_emails} total)[/yellow]")
        
        # Run analysis with enhanced progress indicator
        from rich.progress import BarColumn, TimeRemainingColumn
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Analyzing emails...", total=pending_count)
            
            def update_progress(current, total, subject, status):
                """Progress callback for detailed updates."""
                status_colors = {
                    'analyzing': 'yellow',
                    'summarizing': 'blue', 
                    'saving': 'cyan',
                    'completed': 'green',
                    'error': 'red'
                }
                color = status_colors.get(status, 'white')
                
                if batch_size == 1:  # Show individual email progress only for batch size 1
                    description = f"[{color}]{status.title()}[/{color}] ({current}/{total}): {subject}"
                else:
                    description = f"Analyzing emails... ({current}/{total})"
                
                progress.update(task, completed=current, description=description)
            
            result = await email_service.analyze_saved_emails(batch_size, progress_callback=update_progress)
        
        # Show results
        if result['analyzed'] > 0:
            console.print(f"[green]✅ Successfully analyzed {result['analyzed']} emails![/green]")
        
        if result['errors'] > 0:
            console.print(f"[yellow]⚠️ {result['errors']} emails failed analysis[/yellow]")
        
        # Show updated metadata
        updated_metadata = email_service.get_database_metadata()
        new_analyzed_count = updated_metadata.get('analyzed_count', 0)
        console.print(f"[cyan]📊 Database: {new_analyzed_count}/{total_emails} emails analyzed[/cyan]")
        
        # Show next steps
        console.print(f"\n[bold blue]🔥 Next Steps:[/bold blue]")
        console.print("  • Run [bold]python main.py candidates[/bold] to see deletion recommendations")
        console.print("  • Run [bold]python main.py mark-read --dry-run[/bold] to preview marking trash as read")
        
        # Clean up
        await email_service.close()
        
    except Exception as e:
        console.print(f"[red]Error analyzing emails: {e}[/red]")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--min-score', default=3.0, help='Minimum importance score for candidates (lower = more aggressive deletion)')
@click.option('--limit', '-l', default=20, help='Maximum number of candidates to show')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode with min-score explanation')
@click.pass_context
def candidates(ctx, min_score, limit, interactive):
    """Show emails that are safe deletion candidates."""
    settings = ctx.obj['settings']
    
    if interactive:
        console.print("[bold blue]🗑️ Deletion Candidates Explanation[/bold blue]")
        console.print("\n[yellow]Min-Score Parameter:[/yellow]")
        console.print("• AI scores emails 1-10 for importance")
        console.print("• Lower min-score = more aggressive deletion")
        console.print("• Higher min-score = more conservative deletion")
        console.print("\n[cyan]Score Guidelines:[/cyan]")
        console.print("• -5.0: Very aggressive (deletes most trash) - NEW DEFAULT")
        console.print("• -2.0: Aggressive (deletes clear trash)")
        console.print("• 0.0: Moderate (conservative approach)")
        console.print("• 2.0: Conservative (deletes only obvious spam)")
        console.print("• 5.0: Very conservative (deletes almost nothing)")
        
        console.print(f"\n[yellow]Current min-score: {min_score}[/yellow]")
        
        new_score = click.prompt("\n🎯 Enter preferred min-score (or press Enter to keep current)", 
                                type=float, default=min_score, show_default=True)
        if new_score != min_score:
            min_score = new_score
            console.print(f"[green]✅ Updated min-score to {min_score}[/green]")
        
        console.print(f"\n[bold blue]🗑️ Finding candidates with min-score {min_score}...[/bold blue]")
    else:
        console.print("[bold blue]🗑️ Finding deletion candidates...[/bold blue]")
    
    try:
        # Initialize service
        email_service = EmailApplicationService()
        
        # Get deletion candidates
        candidates = email_service.get_deletion_candidates(min_score)
        
        if not candidates:
            console.print("[green]🛡️ No emails recommended for deletion.[/green]")
            console.print("All your emails appear to be important or haven't been analyzed yet.")
            console.print("\nTry:")
            console.print("• Run [bold]python main.py analyze[/bold] if you haven't analyzed emails yet")
            console.print("• Lower the --min-score threshold (e.g., --min-score -5)")
            return
        
        console.print(f"[yellow]Found {len(candidates)} deletion candidates[/yellow]")
        
        # Create table for candidates
        table = Table(title=f"🗑️ Safe Deletion Candidates (Score ≤ {min_score})")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Date", style="cyan", width=12)
        table.add_column("From", style="magenta", max_width=20)
        table.add_column("Subject", style="white", max_width=35)
        table.add_column("Score", style="red", width=6)
        table.add_column("Reasons", style="dim", max_width=30)
        
        # Show limited number
        displayed_candidates = candidates[:limit]
        
        for i, email in enumerate(displayed_candidates, 1):
            # Parse date
            try:
                from datetime import datetime
                date_str = email.date
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_display = dt.strftime('%m/%d %H:%M')
                else:
                    date_display = date_str[:10]
            except:
                date_display = email.date[:10] if email.date else 'Unknown'
            
            # Clean sender
            sender = email.sender
            if '<' in sender:
                sender = sender.split('<')[0].strip()
            
            # Get reasons
            reasons = ' | '.join(email.importance_score.reasons[:2])
            
            table.add_row(
                str(i),
                date_display,
                sender[:20],
                email.subject[:35],
                f"{email.importance_score.score:.1f}",
                reasons[:30]
            )
        
        console.print(table)
        
        if len(candidates) > limit:
            console.print(f"[dim]... and {len(candidates) - limit} more candidates[/dim]")
        
        # Show category-based summary (preview of what would be deleted)
        preview_summary = email_service.generate_deletion_summary(candidates)
        console.print(f"\n[bold cyan]📊 Deletion Preview by Category:[/bold cyan]")
        
        if preview_summary['categories']:
            # Sort categories by count (descending)
            sorted_categories = sorted(
                preview_summary['categories'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            
            for category, info in sorted_categories:
                count = info['count']
                label = info['label']
                console.print(f"  • [yellow]{count}[/yellow] {label}")
                
                # Show examples for the top categories
                if count >= 3 and info['examples']:
                    example_senders = [ex['sender'][:20] for ex in info['examples'][:2]]
                    console.print(f"    [dim]Examples: {', '.join(example_senders)}[/dim]")
        
        # Show size estimate
        if preview_summary['total_size_mb'] > 0:
            console.print(f"  • [cyan]Estimated space savings: {preview_summary['total_size_mb']} MB[/cyan]")
        
        # Show importance level breakdown
        console.print(f"\n[bold cyan]📊 By Importance Level:[/bold cyan]")
        level_counts = {}
        for email in candidates:
            level = email.importance_score.level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        for level, count in level_counts.items():
            color = {
                'SPAM': 'red',
                'LOW': 'yellow',
                'MEDIUM': 'blue'
            }.get(level, 'white')
            console.print(f"  • [{color}]{level}[/{color}]: {count} emails")
        
        # Show next steps
        console.print(f"\n[bold blue]🔥 Next Steps:[/bold blue]")
        console.print("  • Review the candidates above carefully")
        console.print("  • Run [bold]python main.py mark-read --dry-run[/bold] to preview marking as read")
        console.print("  • Run [bold]python main.py mark-read --confirm[/bold] to actually mark as read")
        
    except Exception as e:
        console.print(f"[red]Error finding deletion candidates: {e}[/red]")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--dry-run', is_flag=True, help='Preview marking as read without actually doing it')
@click.option('--confirm', is_flag=True, help='Actually mark emails as read (no additional confirmation)')
@click.option('--min-score', default=3.0, help='Minimum score threshold for marking as read (lower = more aggressive)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode with explanations')
@click.pass_context
def mark_read(ctx, dry_run, confirm, min_score, interactive):
    """Mark trash emails as read to clean up unread count."""
    asyncio.run(_mark_read_async(ctx, dry_run, confirm, min_score, interactive))

async def _mark_read_async(ctx, dry_run, confirm, min_score, interactive):
    settings = ctx.obj['settings']
    
    if interactive:
        console.print("[bold blue]📧 Mark as Read Explanation[/bold blue]")
        console.print("\n[yellow]What this does:[/yellow]")
        console.print("• Marks trash emails as 'read' in Gmail (not deleted)")
        console.print("• Reduces your unread count")
        console.print("• Emails stay in inbox but no longer appear unread")
        console.print("• Safe operation - you can always mark them unread again")
        
        console.print(f"\n[cyan]Current min-score: {min_score}[/cyan]")
        console.print("• Lower scores = more emails marked as read")
        console.print("• Higher scores = fewer emails marked as read")
        
        if not dry_run and not confirm:
            console.print("\n[yellow]Mode Selection:[/yellow]")
            console.print("• --dry-run: Preview which emails will be marked as read")
            console.print("• --confirm: Actually mark the emails as read")
            
            if click.confirm("\n🔍 Do you want to run in preview mode first?"):
                dry_run = True
                console.print("[green]✅ Running in preview mode[/green]")
            elif click.confirm("🔥 Do you want to mark emails as read now?"):
                confirm = True
                console.print("[yellow]⚠️ Running in confirm mode[/yellow]")
            else:
                console.print("[red]❌ No action selected, exiting[/red]")
                return
    
    if dry_run:
        console.print("[bold blue]🔍 DRY RUN - Preview marking as read (no emails will be changed)[/bold blue]")
    elif confirm:
        console.print("[bold yellow]📧 MARK AS READ MODE - This will mark trash emails as read[/bold yellow]")
    else:
        console.print("[red]❌ You must specify either --dry-run or --confirm[/red]")
        console.print("Use --dry-run to preview or --confirm to actually mark as read")
        return
    
    try:
        # Initialize services
        gmail_client = GmailClient(settings) if confirm else None
        email_service = EmailApplicationService(gmail_client)
        
        # Get deletion candidates
        candidates = email_service.get_deletion_candidates(min_score)
        
        if not candidates:
            console.print("[green]🛡️ No emails meet criteria for marking as read.[/green]")
            console.print(f"No emails found with score ≤ {min_score} that are marked safe to process.")
            return
        
        console.print(f"[yellow]Found {len(candidates)} emails to mark as read[/yellow]")
        
        # Show candidates table
        table = Table(title=f"📧 Emails to Mark as Read (Score ≤ {min_score})")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Date", style="cyan", width=12)
        table.add_column("From", style="magenta", max_width=20)
        table.add_column("Subject", style="white", max_width=40)
        table.add_column("Score", style="red", width=6)
        table.add_column("Level", style="red", width=8)
        
        for i, email in enumerate(candidates, 1):
            # Parse date
            try:
                from datetime import datetime
                date_str = email.date
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_display = dt.strftime('%m/%d %H:%M')
                else:
                    date_display = date_str[:10]
            except:
                date_display = email.date[:10] if email.date else 'Unknown'
            
            # Clean sender
            sender = email.sender
            if '<' in sender:
                sender = sender.split('<')[0].strip()
            
            table.add_row(
                str(i),
                date_display,
                sender[:20],
                email.subject[:40],
                f"{email.importance_score.score:.1f}",
                email.importance_score.level.value
            )
        
        console.print(table)
        
        # Calculate savings
        total_size = sum(email.size_estimate for email in candidates)
        size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
        
        console.print(f"\n[bold cyan]📊 Mark as Read Summary:[/bold cyan]")
        console.print(f"  • Total emails: {len(candidates)}")
        console.print(f"  • These emails will be marked as read (not deleted)")
        
        if dry_run:
            console.print(f"\n[bold green]✅ DRY RUN COMPLETE[/bold green]")
            console.print("To actually mark these emails as read, run:")
            console.print("[bold]python main.py mark-read --confirm[/bold]")
            return
        
        # Perform marking as read
        if confirm:
            console.print(f"\n[bold yellow]📧 PROCEEDING TO MARK AS READ[/bold yellow]")
            console.print(f"Marking {len(candidates)} emails as READ...")
            console.print("They will no longer appear in your unread count.")
            
            # Perform actual marking as read
            console.print(f"\n[bold yellow]📧 Processing {len(candidates)} emails...[/bold yellow]")
            
            processed_count = 0
            failed_count = 0
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Marking {len(candidates)} emails as read...", total=len(candidates))
                
                for email in candidates:
                    try:
                        # Mark email as read via Gmail API
                        gmail_client.service.users().messages().modify(
                            userId='me', 
                            id=email.id,
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                        
                        processed_count += 1
                        progress.advance(task)
                        
                    except Exception as e:
                        logger.error(f"Failed to mark email {email.id} as read: {e}")
                        failed_count += 1
                        progress.advance(task)
            
            # Generate and show categorized summary
            successfully_marked = [email for i, email in enumerate(candidates) if i < processed_count]
            summary = email_service.generate_deletion_summary(successfully_marked)
            summary_lines = email_service.format_deletion_summary_for_display(summary)
            
            console.print(f"\n[bold green]✅ MARK AS READ COMPLETE[/bold green]")
            for line in summary_lines:
                console.print(line)
            
            if failed_count > 0:
                console.print(f"\n[yellow]⚠️ Failed to process: {failed_count} emails[/yellow]")
            
            console.print(f"\n[bold blue]📧 Final Result:[/bold blue]")
            console.print(f"  • Your unread count has been reduced by {processed_count}")
            console.print(f"  • Emails are still in your inbox but marked as read")
        
        # Clean up
        if email_service:
            await email_service.close()
        
    except Exception as e:
        console.print(f"[red]Error during mark as read operation: {e}[/red]")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--max-emails', '-m', default=50, help='Maximum number of unread emails to fetch')
@click.option('--min-score', default=3.0, help='Minimum score threshold for marking as read (lower = more aggressive)')
@click.option('--dry-run', is_flag=True, help='Preview the entire workflow without making changes')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode with explanations and confirmations')
@click.pass_context
def auto(ctx, max_emails, min_score, dry_run, interactive):
    """Run the complete workflow: fetch → analyze → mark-read automatically."""
    asyncio.run(_auto_async(ctx, max_emails, min_score, dry_run, interactive))

async def _auto_async(ctx, max_emails, min_score, dry_run, interactive):
    """Run the complete automated workflow."""
    settings = ctx.obj['settings']
    
    if interactive:
        console.print("[bold blue]🤖 Full Auto Workflow Explanation[/bold blue]")
        console.print("\n[yellow]This will automatically:[/yellow]")
        console.print("1. 📧 Fetch unread emails from Gmail")
        console.print("2. 🤖 Analyze all emails with AI")
        console.print("3. 🗑️ Mark trash emails as read")
        console.print("4. ✅ Show you the results")
        
        console.print(f"\n[cyan]Settings:[/cyan]")
        console.print(f"• Max emails: {max_emails}")
        console.print(f"• Min-score: {min_score} (lower = more aggressive)")
        console.print(f"• Mode: {'Preview only' if dry_run else 'Will make changes'}")
        
        if not click.confirm("\n🚀 Continue with auto workflow?"):
            console.print("[yellow]❌ Auto workflow cancelled[/yellow]")
            return
        
        console.print("\n[bold green]🚀 Starting automated workflow...[/bold green]")
    else:
        console.print("[bold blue]🤖 Running automated email cleanup workflow...[/bold blue]")
    
    try:
        # Step 1: Fetch unread emails
        console.print("\n[bold blue]📧 Step 1: Fetching unread emails...[/bold blue]")
        gmail_client = GmailClient(settings)
        config = AnalysisConfig()
        email_service = EmailApplicationService(gmail_client, config)
        
        domain_emails = email_service.fetch_and_save_unread_emails(max_results=max_emails)
        
        if not domain_emails:
            console.print("[green]🎉 No unread emails! Your inbox is clean.[/green]")
            return
        
        console.print(f"[green]✅ Found {len(domain_emails)} unread emails[/green]")
        
        # Step 2: Analyze emails
        console.print("\n[bold blue]🤖 Step 2: Analyzing emails with AI...[/bold blue]")
        
        # Use smaller batch size for better progress visibility in auto mode
        from rich.progress import BarColumn, TimeRemainingColumn
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as auto_progress:
            auto_task = auto_progress.add_task(f"Analyzing emails...", total=len(domain_emails))
            
            def auto_update_progress(current, total, subject, status):
                """Progress callback for auto mode."""
                description = f"Analyzing emails... ({current}/{total})"
                auto_progress.update(auto_task, completed=current, description=description)
            
            result = await email_service.analyze_saved_emails(batch_size=5, progress_callback=auto_update_progress)
        
        if result['analyzed'] > 0:
            console.print(f"[green]✅ Analyzed {result['analyzed']} emails[/green]")
        else:
            console.print("[yellow]⚠️ No emails were analyzed[/yellow]")
            return
        
        # Step 3: Find candidates
        console.print("\n[bold blue]🗑️ Step 3: Finding deletion candidates...[/bold blue]")
        candidates = email_service.get_deletion_candidates(min_score)
        
        if not candidates:
            console.print("[green]🛡️ No emails recommended for marking as read.[/green]")
            console.print("All your emails appear to be important!")
            return
        
        console.print(f"[yellow]Found {len(candidates)} emails to mark as read[/yellow]")
        
        # Show candidates table
        formatted_candidates = email_service.format_emails_for_display(candidates)
        
        table = Table(title=f"🗑️ Emails to Mark as Read (Score ≤ {min_score})")
        table.add_column("#", style="cyan", width=3)
        table.add_column("From", style="magenta", max_width=20)
        table.add_column("Subject", style="white", max_width=40)
        table.add_column("Score", style="red", width=6)
        
        for i, email in enumerate(formatted_candidates[:10], 1):  # Show first 10
            table.add_row(
                str(i),
                email['sender'][:20],
                email['subject'][:40],
                f"{email['importance']['score']:.1f}"
            )
        
        console.print(table)
        
        if len(candidates) > 10:
            console.print(f"[dim]... and {len(candidates) - 10} more candidates[/dim]")
        
        # Step 4: Mark as read (or preview)
        if dry_run:
            console.print(f"\n[bold green]✅ DRY RUN COMPLETE[/bold green]")
            console.print(f"Found {len(candidates)} emails that would be marked as read")
            console.print("To actually mark them as read, run:")
            console.print("[bold]python main.py auto --confirm[/bold]")
        else:
            console.print(f"\n[bold yellow]📧 Step 4: Marking {len(candidates)} emails as read...[/bold yellow]")
            
            if interactive and not click.confirm(f"Mark {len(candidates)} emails as read?"):
                console.print("[yellow]❌ Marking as read cancelled[/yellow]")
                return
            
            # Mark emails as read
            processed_count = 0
            failed_count = 0
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Marking {len(candidates)} emails as read...", total=len(candidates))
                
                for email in candidates:
                    try:
                        gmail_client.service.users().messages().modify(
                            userId='me', 
                            id=email.id,
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                        
                        processed_count += 1
                        progress.advance(task)
                        
                    except Exception as e:
                        logger.error(f"Failed to mark email {email.id} as read: {e}")
                        failed_count += 1
                        progress.advance(task)
            
            # Generate and show categorized summary
            successfully_marked = [email for i, email in enumerate(candidates) if i < processed_count]
            summary = email_service.generate_deletion_summary(successfully_marked)
            summary_lines = email_service.format_deletion_summary_for_display(summary)
            
            console.print(f"\n[bold green]🎉 AUTO WORKFLOW COMPLETE![/bold green]")
            for line in summary_lines:
                console.print(line)
            
            if failed_count > 0:
                console.print(f"\n[yellow]⚠️ Failed to process {failed_count} emails[/yellow]")
            
            console.print(f"\n[bold blue]📧 Final Result:[/bold blue]")
            console.print(f"• Started with: {len(domain_emails)} unread emails")
            console.print(f"• Marked as read: {processed_count} trash emails")
            console.print(f"• Remaining unread: {len(domain_emails) - processed_count} important emails")
        
        # Clean up
        await email_service.close()
        
    except Exception as e:
        console.print(f"[red]Error during auto workflow: {e}[/red]")
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
        console.print("• Run 'python main.py unread' to fetch and save unread emails")
        
    except Exception as e:
        console.print(f"[red]❌ Setup failed: {e}[/red]")
        console.print("\nPlease check:")
        console.print("1. Gmail API credentials are in config/credentials.json")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli()
