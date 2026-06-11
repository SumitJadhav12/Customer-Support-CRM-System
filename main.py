from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import sqlite3
import os
import re
from datetime import datetime

app = FastAPI(title="Support CRM System")

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

# Database setup
def get_db():
    conn = sqlite3.connect("tickets.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (status IN ('Open', 'In Progress', 'Closed'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            note_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Helper: Generate ticket ID
def generate_ticket_id():
    conn = get_db()
    cursor = conn.execute("SELECT ticket_id FROM tickets")
    ids = cursor.fetchall()
    conn.close()
    max_num = 0
    for row in ids:
        match = re.search(r'TKT-(\d+)', row["ticket_id"])
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    next_num = max_num + 1
    return f"TKT-{next_num:03d}"

# Pydantic Models
class TicketCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_email: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)

    @validator("customer_email")
    def validate_email(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email address")
        return v

class TicketUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        if v not in ["Open", "In Progress", "Closed"]:
            raise ValueError("Invalid status")
        return v

# API Endpoints
@app.post("/api/tickets")
async def create_ticket(ticket: TicketCreate):
    conn = get_db()
    ticket_id = generate_ticket_id()
    try:
        conn.execute("""
            INSERT INTO tickets (ticket_id, customer_name, customer_email, subject, description)
            VALUES (?, ?, ?, ?, ?)
        """, (ticket_id, ticket.customer_name, ticket.customer_email, ticket.subject, ticket.description))
        conn.commit()
        return {"ticket_id": ticket_id, "created_at": datetime.now().isoformat()}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/api/tickets")
async def list_tickets(
    status: Optional[str] = Query(None),
    search: Optional[str] = None
):
    conn = get_db()
    query = "SELECT ticket_id, customer_name, subject, status, created_at FROM tickets WHERE 1=1"
    params = []
    
    if status and status != "all":
        query += " AND status = ?"
        params.append(status)
    
    if search:
        query += """ AND (
            customer_name LIKE ? OR 
            ticket_id LIKE ? OR 
            customer_email LIKE ? OR 
            subject LIKE ? OR 
            description LIKE ?
        )"""
        search_param = f"%{search}%"
        params.extend([search_param] * 5)
    
    query += " ORDER BY created_at DESC"
    
    cursor = conn.execute(query, params)
    tickets = cursor.fetchall()
    conn.close()
    
    return [dict(t) for t in tickets]

@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    conn = get_db()
    ticket = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    notes = conn.execute(
        "SELECT note_text, created_at FROM notes WHERE ticket_id = ? ORDER BY created_at DESC",
        (ticket_id,)
    ).fetchall()
    conn.close()
    
    result = dict(ticket)
    result["notes"] = [dict(n) for n in notes]
    return result

@app.put("/api/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, update: TicketUpdate):
    conn = get_db()
    ticket = conn.execute("SELECT ticket_id FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    try:
        conn.execute(
            "UPDATE tickets SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?",
            (update.status, ticket_id)
        )
        if update.notes and update.notes.strip():
            conn.execute(
                "INSERT INTO notes (ticket_id, note_text) VALUES (?, ?)",
                (ticket_id, update.notes.strip())
            )
        conn.commit()
        return {"success": True, "updated_at": datetime.now().isoformat()}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# Serve Frontend - Root endpoint
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    html_path = "static/index.html"
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("""
    <html>
        <head><title>Support CRM</title></head>
        <body style="font-family: Arial; text-align: center; margin-top: 50px;">
            <h1>🚀 Support CRM System</h1>
            <p>API is running successfully!</p>
            <p>📖 <a href="/docs">View API Documentation</a></p>
            <p>✅ Status: <span style="color: green;">Online</span></p>
        </body>
    </html>
    """)

# API Documentation endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
