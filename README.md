# 🎫 Support CRM System

A full-stack customer support ticket management system built with FastAPI, SQLite, and Tailwind CSS.

## Features

- ✅ Create tickets with auto-generated ID (TKT-001 format)
- ✅ List all tickets in clean table view
- ✅ Real-time search across all fields
- ✅ Filter by status (Open, In Progress, Closed)
- ✅ View detailed ticket information
- ✅ Update status and add notes/comments
- ✅ Notes history with timestamps
- ✅ Mobile-responsive design

## Tech Stack

- **Backend**: Python FastAPI
- **Database**: SQLite
- **Frontend**: HTML5 + Tailwind CSS + Vanilla JS
- **Deployment**: Railway.app

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tickets` | Create a new ticket |
| GET | `/api/tickets` | List all tickets (supports search & filter) |
| GET | `/api/tickets/{id}` | Get ticket details with notes |
| PUT | `/api/tickets/{id}` | Update status and add note |
| GET | `/health` | Health check endpoint |

## Local Development

```bash
# Clone repository
git clone https://github.com/SumitJadhav12/Customer-Support-CRM-System.git
cd Customer-Support-CRM-System

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
uvicorn main:app --reload --port 8000