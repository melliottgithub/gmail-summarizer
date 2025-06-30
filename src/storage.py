"""
Email storage and database management
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class EmailStorage:
    """Handle email storage and retrieval using SQLite."""
    
    def __init__(self, settings):
        """Initialize storage with settings."""
        self.settings = settings
        self.db_path = settings.database_path
        self._ensure_directory()
        self.initialize()
    
    def _ensure_directory(self):
        """Ensure the data directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def initialize(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    date TEXT,
                    sender TEXT,
                    recipient TEXT,
                    subject TEXT,
                    text_body TEXT,
                    html_body TEXT,
                    labels TEXT,
                    relevance_score REAL,
                    category TEXT,
                    attachments TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_date TEXT,
                    end_date TEXT,
                    summary_text TEXT,
                    style TEXT,
                    email_count INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category)')
            
            conn.commit()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def store_emails(self, emails: List[Dict[str, Any]]) -> int:
        """
        Store emails in the database.
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            Number of emails stored
        """
        stored_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            for email in emails:
                try:
                    # Check if email already exists
                    existing = conn.execute(
                        'SELECT id FROM emails WHERE id = ?', 
                        (email['id'],)
                    ).fetchone()
                    
                    if existing:
                        logger.debug(f"Email {email['id']} already exists, skipping")
                        continue
                    
                    # Insert new email
                    conn.execute('''
                        INSERT INTO emails (
                            id, thread_id, date, sender, recipient, subject,
                            text_body, html_body, labels, relevance_score,
                            category, attachments, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        email['id'],
                        email.get('thread_id', ''),
                        email.get('date', ''),
                        email.get('sender', ''),
                        email.get('recipient', ''),
                        email.get('subject', ''),
                        email.get('text_body', ''),
                        email.get('html_body', ''),
                        json.dumps(email.get('labels', [])),
                        email.get('relevance_score', 0.0),
                        email.get('category', 'other'),
                        json.dumps(email.get('attachments', [])),
                        json.dumps({
                            'size_estimate': email.get('size_estimate', 0),
                            'snippet': email.get('snippet', ''),
                            'cc': email.get('cc', ''),
                            'bcc': email.get('bcc', ''),
                            'reply_to': email.get('reply_to', ''),
                            'message_id': email.get('message_id', ''),
                            'in_reply_to': email.get('in_reply_to', ''),
                            'references': email.get('references', '')
                        })
                    ))
                    stored_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to store email {email.get('id', 'unknown')}: {e}")
                    continue
            
            conn.commit()
        
        logger.info(f"Stored {stored_count} new emails")
        return stored_count
    
    def get_emails(self, start_date: datetime, end_date: datetime, 
                   category: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve emails from storage.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            category: Optional category filter
            limit: Optional limit on number of results
            
        Returns:
            List of email dictionaries
        """
        query = '''
            SELECT * FROM emails 
            WHERE date >= ? AND date <= ?
        '''
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        query += ' ORDER BY date DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        emails = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            for row in cursor.fetchall():
                email = dict(row)
                # Parse JSON fields
                email['labels'] = json.loads(email['labels'] or '[]')
                email['attachments'] = json.loads(email['attachments'] or '[]')
                email['metadata'] = json.loads(email['metadata'] or '{}')
                emails.append(email)
        
        logger.info(f"Retrieved {len(emails)} emails from storage")
        return emails
    
    def store_summary(self, summary_text: str, start_date: datetime, 
                     end_date: datetime, style: str, email_count: int = None):
        """Store a generated summary."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO summaries (
                    start_date, end_date, summary_text, style, email_count
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                start_date.isoformat(),
                end_date.isoformat(),
                summary_text,
                style,
                email_count or 0
            ))
            conn.commit()
        
        logger.info("Summary stored successfully")
    
    def get_summaries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent summaries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM summaries 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total_emails = conn.execute('SELECT COUNT(*) FROM emails').fetchone()[0]
            total_summaries = conn.execute('SELECT COUNT(*) FROM summaries').fetchone()[0]
            
            # Get email counts by category
            category_counts = {}
            cursor = conn.execute('SELECT category, COUNT(*) FROM emails GROUP BY category')
            for category, count in cursor.fetchall():
                category_counts[category] = count
            
            # Get date range
            date_range = conn.execute('''
                SELECT MIN(date) as earliest, MAX(date) as latest 
                FROM emails
            ''').fetchone()
            
            return {
                'total_emails': total_emails,
                'total_summaries': total_summaries,
                'category_counts': category_counts,
                'earliest_email': date_range[0] if date_range[0] else None,
                'latest_email': date_range[1] if date_range[1] else None
            }
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data from storage."""
        cutoff_date = datetime.now().replace(day=1) - \
                     datetime.timedelta(days=days_to_keep)
        
        with sqlite3.connect(self.db_path) as conn:
            # Remove old emails
            result = conn.execute('''
                DELETE FROM emails 
                WHERE date < ?
            ''', (cutoff_date.isoformat(),))
            
            emails_deleted = result.rowcount
            
            # Remove old summaries
            result = conn.execute('''
                DELETE FROM summaries 
                WHERE created_at < ?
            ''', (cutoff_date.isoformat(),))
            
            summaries_deleted = result.rowcount
            conn.commit()
        
        logger.info(f"Cleaned up {emails_deleted} old emails and {summaries_deleted} old summaries")
        return emails_deleted, summaries_deleted
