import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from app.models.ticket import Ticket

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'helpdesk.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database and creates the required tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Tickets Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        email TEXT NOT NULL,
        source TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        created_time TEXT NOT NULL,
        status TEXT NOT NULL,
        priority TEXT NOT NULL,
        category TEXT NOT NULL,
        confidence REAL NOT NULL,
        language TEXT NOT NULL,
        entities TEXT, -- JSON string
        sentiment TEXT NOT NULL,
        is_spam INTEGER NOT NULL DEFAULT 0,
        original_body TEXT,
        assigned_team TEXT,
        merged_with TEXT,
        attachment_name TEXT
    )
    ''')
    
    # 2. Customers Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        email TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT
    )
    ''')
    
    # 3. Attachments Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_data BLOB,
        FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
    )
    ''')
    
    # 4. Predictions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        ticket_id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        confidence REAL NOT NULL,
        probabilities TEXT, -- JSON string
        FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
    )
    ''')
    
    # 5. Activity Logs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT NOT NULL,
        action TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        details TEXT,
        FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()

class TicketRepository:
    @staticmethod
    def get_next_ticket_id() -> str:
        """Generates the next sequential ticket ID in the format SUP-2026-000145."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ticket_id FROM tickets WHERE ticket_id LIKE 'SUP-2026-%' ORDER BY ticket_id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        current_year = "2026"
        if row:
            last_id = row['ticket_id']
            # Extract sequence number
            try:
                seq = int(last_id.split('-')[-1])
                next_seq = seq + 1
            except ValueError:
                next_seq = 1
        else:
            next_seq = 1
            
        return f"SUP-{current_year}-{next_seq:06d}"

    @staticmethod
    def save_ticket(ticket: Ticket) -> str:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Save customer if not exists
        cursor.execute("INSERT OR IGNORE INTO customers (email, name) VALUES (?, ?)", 
                       (ticket.email, ticket.customer_name))
        
        # Save ticket
        cursor.execute('''
        INSERT OR REPLACE INTO tickets (
            ticket_id, customer_name, email, source, subject, body, created_time,
            status, priority, category, confidence, language, entities, sentiment,
            is_spam, original_body, assigned_team, merged_with, attachment_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticket.ticket_id, ticket.customer_name, ticket.email, ticket.source,
            ticket.subject, ticket.body, ticket.created_time, ticket.status,
            ticket.priority, ticket.category, ticket.confidence, ticket.language,
            json.dumps(ticket.entities), ticket.sentiment, 1 if ticket.is_spam else 0,
            ticket.original_body, ticket.assigned_team, ticket.merged_with, ticket.attachment_name
        ))
        
        # Save attachment if present
        if ticket.attachment_name and ticket.attachment_data:
            cursor.execute('''
            INSERT INTO attachments (ticket_id, filename, file_data)
            VALUES (?, ?, ?)
            ''', (ticket.ticket_id, ticket.attachment_name, ticket.attachment_data))
            
        # Log ticket creation activity
        cursor.execute('''
        INSERT INTO activity_logs (ticket_id, action, timestamp, details)
        VALUES (?, 'Created', datetime('now', 'localtime'), ?)
        ''', (ticket.ticket_id, f"Ticket created via {ticket.source}"))
        
        conn.commit()
        conn.close()
        return ticket.ticket_id

    @staticmethod
    def get_ticket(ticket_id: str) -> Optional[Ticket]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return Ticket(
            ticket_id=row['ticket_id'],
            customer_name=row['customer_name'],
            email=row['email'],
            source=row['source'],
            subject=row['subject'],
            body=row['body'],
            created_time=row['created_time'],
            status=row['status'],
            priority=row['priority'],
            category=row['category'],
            confidence=row['confidence'],
            language=row['language'],
            entities=json.loads(row['entities']) if row['entities'] else {},
            sentiment=row['sentiment'],
            is_spam=bool(row['is_spam']),
            original_body=row['original_body'],
            assigned_team=row['assigned_team'],
            merged_with=row['merged_with'],
            attachment_name=row['attachment_name']
        )

    @staticmethod
    def list_tickets(search: str = "", category: str = "All", priority: str = "All", status: str = "All", sort_by: str = "created_time", sort_order: str = "DESC") -> List[Ticket]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM tickets WHERE 1=1"
        params = []
        
        if search:
            query += " AND (subject LIKE ? OR body LIKE ? OR customer_name LIKE ? OR ticket_id LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
            
        if category != "All":
            query += " AND category = ?"
            params.append(category)
            
        if priority != "All":
            query += " AND priority = ?"
            params.append(priority)
            
        if status != "All":
            query += " AND status = ?"
            params.append(status)
            
        # Sorting
        allowed_sort_fields = {"created_time", "priority", "category", "status", "confidence", "ticket_id"}
        if sort_by not in allowed_sort_fields:
            sort_by = "created_time"
            
        sort_order = "DESC" if sort_order.upper() == "DESC" else "ASC"
        query += f" ORDER BY {sort_by} {sort_order}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        tickets = []
        for row in rows:
            tickets.append(Ticket(
                ticket_id=row['ticket_id'],
                customer_name=row['customer_name'],
                email=row['email'],
                source=row['source'],
                subject=row['subject'],
                body=row['body'],
                created_time=row['created_time'],
                status=row['status'],
                priority=row['priority'],
                category=row['category'],
                confidence=row['confidence'],
                language=row['language'],
                entities=json.loads(row['entities']) if row['entities'] else {},
                sentiment=row['sentiment'],
                is_spam=bool(row['is_spam']),
                original_body=row['original_body'],
                assigned_team=row['assigned_team'],
                merged_with=row['merged_with'],
                attachment_name=row['attachment_name']
            ))
        return tickets

    @staticmethod
    def update_ticket_status(ticket_id: str, status: str) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tickets SET status = ? WHERE ticket_id = ?", (status, ticket_id))
        cursor.execute("INSERT INTO activity_logs (ticket_id, action, timestamp, details) VALUES (?, 'Status Change', datetime('now', 'localtime'), ?)",
                       (ticket_id, f"Status updated to {status}"))
        conn.commit()
        conn.close()

    @staticmethod
    def update_ticket(ticket: Ticket) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE tickets SET 
            status = ?, priority = ?, category = ?, confidence = ?, 
            assigned_team = ?, merged_with = ?
        WHERE ticket_id = ?
        ''', (
            ticket.status, ticket.priority, ticket.category, ticket.confidence,
            ticket.assigned_team, ticket.merged_with, ticket.ticket_id
        ))
        cursor.execute("INSERT INTO activity_logs (ticket_id, action, timestamp, details) VALUES (?, 'Updated', datetime('now', 'localtime'), 'Ticket attributes updated')",
                       (ticket.ticket_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def save_prediction(ticket_id: str, category: str, confidence: float, probabilities: Dict[str, float]) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO predictions (ticket_id, category, confidence, probabilities)
        VALUES (?, ?, ?, ?)
        ''', (ticket_id, category, confidence, json.dumps(probabilities)))
        conn.commit()
        conn.close()

    @staticmethod
    def get_prediction(ticket_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE ticket_id = ?", (ticket_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return {
            "ticket_id": row['ticket_id'],
            "category": row['category'],
            "confidence": row['confidence'],
            "probabilities": json.loads(row['probabilities'])
        }

    @staticmethod
    def get_activity_logs(ticket_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activity_logs WHERE ticket_id = ? ORDER BY timestamp DESC", (ticket_id,))
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append({
                "action": row['action'],
                "timestamp": row['timestamp'],
                "details": row['details']
            })
        return logs

    @staticmethod
    def get_dashboard_metrics() -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        metrics = {}
        
        # Today's Tickets
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE date(created_time) = date('now', 'localtime')")
        metrics['todays_tickets'] = cursor.fetchone()[0]
        
        # Open
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Open'")
        metrics['open_tickets'] = cursor.fetchone()[0]
        
        # Resolved
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Resolved'")
        metrics['resolved_tickets'] = cursor.fetchone()[0]
        
        # Pending
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Pending'")
        metrics['pending_tickets'] = cursor.fetchone()[0]
        
        # Average Confidence
        cursor.execute("SELECT AVG(confidence) FROM tickets WHERE confidence > 0")
        val = cursor.fetchone()[0]
        metrics['avg_confidence'] = val if val is not None else 0.0
        
        # Avg Response Time (Simulated)
        metrics['avg_response_time'] = "2.4 Hours"
        
        conn.close()
        return metrics
