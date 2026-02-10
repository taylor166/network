"""
Message storage layer using SQLite.

This is designed to be swappable - you could replace this with PostgreSQL,
MongoDB, or another storage solution later.
"""
import sqlite3
import os
from typing import List, Optional
from datetime import datetime
from contextlib import contextmanager
import logging

from contacts.message_models import (
    MessageCreate, MessageResponse, MessageFilter,
    MessageDirection, MessageChannel
)

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "messages.db")


def get_db_path() -> str:
    """Get the database file path, creating directories if needed."""
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    return DB_PATH


@contextmanager
def get_db_connection():
    """Get a database connection with proper error handling."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_message_db():
    """Initialize the messages database with required tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id TEXT NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('inbound', 'outbound')),
                channel TEXT NOT NULL CHECK(channel IN ('email', 'sms')),
                subject TEXT,
                body TEXT NOT NULL,
                from_address TEXT,
                to_address TEXT,
                from_phone TEXT,
                to_phone TEXT,
                thread_id TEXT,
                provider_message_id TEXT,
                from_account TEXT,
                sent_at TIMESTAMP,
                received_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add from_account column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN from_account TEXT")
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        # Create indexes separately (SQLite doesn't support INDEX in CREATE TABLE)
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_contact_id ON messages(contact_id)",
            "CREATE INDEX IF NOT EXISTS idx_direction ON messages(direction)",
            "CREATE INDEX IF NOT EXISTS idx_channel ON messages(channel)",
            "CREATE INDEX IF NOT EXISTS idx_thread_id ON messages(thread_id)",
            "CREATE INDEX IF NOT EXISTS idx_provider_message_id ON messages(provider_message_id)",
            "CREATE INDEX IF NOT EXISTS idx_created_at ON messages(created_at)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        logger.info("Message database initialized")


class MessageStorage:
    """Storage layer for messages."""
    
    def __init__(self):
        """Initialize storage and ensure database exists."""
        init_message_db()
    
    def create_message(self, message: MessageCreate) -> MessageResponse:
        """Create a new message record."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Set timestamps
            sent_at = message.sent_at or (datetime.utcnow() if message.direction == MessageDirection.OUTBOUND else None)
            received_at = message.received_at or (datetime.utcnow() if message.direction == MessageDirection.INBOUND else None)
            created_at = datetime.utcnow()
            
            # Extract from_account from message (stored in from_address for outbound, or as separate field)
            from_account = getattr(message, 'from_account', None)
            if not from_account and message.direction == MessageDirection.OUTBOUND:
                from_account = message.from_address
            
            cursor.execute("""
                INSERT INTO messages (
                    contact_id, direction, channel, subject, body,
                    from_address, to_address, from_phone, to_phone,
                    thread_id, provider_message_id, from_account,
                    sent_at, received_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.contact_id,
                message.direction.value,
                message.channel.value,
                message.subject,
                message.body,
                message.from_address,
                message.to_address,
                message.from_phone,
                message.to_phone,
                message.thread_id,
                message.provider_message_id,
                from_account,
                sent_at.isoformat() if sent_at else None,
                received_at.isoformat() if received_at else None,
                created_at.isoformat()
            ))
            
            message_id = cursor.lastrowid
            
            # Fetch the created message
            cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
            row = cursor.fetchone()
            
            return self._row_to_message(row)
    
    def get_message(self, message_id: int) -> Optional[MessageResponse]:
        """Get a message by ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_message(row)
    
    def get_messages(self, filter_params: MessageFilter) -> List[MessageResponse]:
        """Get messages with optional filtering."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM messages WHERE 1=1"
            params = []
            
            if filter_params.contact_id:
                query += " AND contact_id = ?"
                params.append(filter_params.contact_id)
            
            if filter_params.channel:
                query += " AND channel = ?"
                params.append(filter_params.channel.value)
            
            if filter_params.direction:
                query += " AND direction = ?"
                params.append(filter_params.direction.value)
            
            # Filter for CRM-sent emails only (outbox filter)
            if filter_params.crm_sent_only:
                query += " AND from_account IS NOT NULL"
            
            # Filter for responses to CRM emails (inbox filter)
            if filter_params.crm_responses_only:
                # Get all thread_ids from outbound CRM emails
                cursor.execute("""
                    SELECT DISTINCT thread_id FROM messages 
                    WHERE direction = 'outbound' 
                    AND from_account IS NOT NULL 
                    AND thread_id IS NOT NULL
                """)
                crm_thread_ids = [row[0] for row in cursor.fetchall() if row[0]]
                if crm_thread_ids:
                    placeholders = ','.join(['?'] * len(crm_thread_ids))
                    query += f" AND thread_id IN ({placeholders})"
                    params.extend(crm_thread_ids)
                else:
                    # No CRM emails, so no responses
                    query += " AND 1=0"
            
            # Order by created_at descending (newest first)
            query += " ORDER BY created_at DESC"
            
            # Add limit and offset
            if filter_params.limit:
                query += " LIMIT ?"
                params.append(filter_params.limit)
            
            if filter_params.offset:
                query += " OFFSET ?"
                params.append(filter_params.offset)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_message(row) for row in rows]
    
    def get_messages_by_contact(self, contact_id: str, limit: Optional[int] = None) -> List[MessageResponse]:
        """Get all messages for a specific contact."""
        filter_params = MessageFilter(contact_id=contact_id, limit=limit or 100)
        return self.get_messages(filter_params)
    
    def get_message_by_provider_id(self, provider_message_id: str, channel: MessageChannel) -> Optional[MessageResponse]:
        """Get a message by provider message ID (for deduplication)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM messages WHERE provider_message_id = ? AND channel = ?",
                (provider_message_id, channel.value)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_message(row)
    
    def update_message(self, message_id: int, updates: dict) -> Optional[MessageResponse]:
        """Update a message (for syncing additional data)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build update query
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                if value is not None:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
            
            if not set_clauses:
                return None
            
            params.append(message_id)
            query = f"UPDATE messages SET {', '.join(set_clauses)} WHERE id = ?"
            
            cursor.execute(query, params)
            
            # Fetch updated message
            cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_message(row)
    
    def _row_to_message(self, row: sqlite3.Row) -> MessageResponse:
        """Convert a database row to a MessageResponse."""
        def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
            if not dt_str:
                return None
            try:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            except:
                return None
        
        # Get from_account (handle both old and new schema)
        # sqlite3.Row doesn't have .get() method, use bracket notation with key check
        from_account = row["from_account"] if "from_account" in row.keys() else None
        
        msg = MessageResponse(
            id=row["id"],
            contact_id=row["contact_id"],
            direction=MessageDirection(row["direction"]),
            channel=MessageChannel(row["channel"]),
            subject=row["subject"],
            body=row["body"],
            from_address=row["from_address"],
            to_address=row["to_address"],
            from_phone=row["from_phone"],
            to_phone=row["to_phone"],
            thread_id=row["thread_id"],
            provider_message_id=row["provider_message_id"],
            sent_at=parse_datetime(row["sent_at"]),
            received_at=parse_datetime(row["received_at"]),
            created_at=parse_datetime(row["created_at"]) or datetime.utcnow(),
            from_account=from_account
        )
        return msg
    
    def get_crm_thread_ids(self) -> List[str]:
        """Get all thread IDs from CRM-sent emails."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT thread_id FROM messages 
                WHERE direction = 'outbound' 
                AND from_account IS NOT NULL 
                AND thread_id IS NOT NULL
            """)
            return [row[0] for row in cursor.fetchall() if row[0]]
