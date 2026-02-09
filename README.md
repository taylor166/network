# Networking/CRM Tool

An end-to-end networking and CRM tool designed to streamline the process of sourcing contacts, reaching out, scheduling meetings, taking notes, and following up.

## Overview

This tool helps manage the complete networking workflow:

1. **Source** - Find and collect people and their contact information
2. **Reach Out** - Send outreach messages using templates (one-click functionality)
3. **Respond/Schedule** - Handle responses and schedule meetings (integrates with existing EA/Scheduler project)
4. **Take Notes** - Capture and store call notes and meeting summaries
5. **Follow Up** - Automated follow-up reminders based on context and interaction history

## Project Structure

```
networking-crm/
├── AGENTS.md                    # AI assistant instructions
├── README.md                    # This file
├── contacts/
│   ├── api.py                  # FastAPI endpoints
│   ├── notion_client.py        # Notion API integration
│   ├── models.py               # Data models
│   ├── static/                 # Frontend UI
│   ├── SETUP.md                # Setup instructions
│   ├── README.md               # Contact system docs
│   ├── active/                 # Active contacts (legacy)
│   ├── archived/               # Archived contacts (legacy)
│   └── templates/              # Contact templates/formats
├── workflows/
│   ├── outreach/               # Outreach workflow definitions
│   ├── scheduling/             # Scheduling workflow definitions
│   └── followup/               # Follow-up workflow definitions
├── integrations/
│   ├── google-calendar/        # Google Calendar integration
│   ├── email/                  # Email integration
│   └── linkedin/               # LinkedIn integration
├── notes/
│   ├── call-notes/             # Call notes
│   └── meeting-summaries/      # Meeting summaries
├── templates/
│   ├── email/                  # Email templates
│   └── message/                # Message templates (LinkedIn, etc.)
└── data/
    ├── analytics/               # Analytics data
    └── tracking/                # Tracking data
```

## Integration

This tool integrates with an existing EA/Scheduler project that:
- Takes inputs from emails
- Offers available times based on Google Calendar
- Considers timing preferences
- Schedules meetings

## Getting Started

### Contact Management System (Built)

The contact management system is now available! It integrates with Notion as the source of truth.

**Quick Start:**
1. See `contacts/SETUP.md` for detailed setup instructions
2. Install dependencies: 
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Configure Notion integration (add credentials to `.env`)
4. Run the server: `python main.py` (with venv activated) or `python3 main.py`
5. Open `http://localhost:8000` in your browser

**Note:** On macOS, use `python3` and `pip3` instead of `python` and `pip`.

**Features:**
- ✅ Notion integration (bidirectional sync)
- ✅ Add, view, edit, delete contacts
- ✅ Filter by status, type, group, relationship type
- ✅ Search by name, email, company, notes
- ✅ Status workflow management

### Next Components to Build

1. Outreach system (one-click outreach using templates)
2. Scheduling integration (with existing EA/Scheduler)
3. Notes system (call notes and meeting summaries)
4. Follow-up automation

## Development Approach

- Build incrementally, one component at a time
- Focus on workflows and structure first
- Integrate with existing systems
- Track data throughout the workflow for context-aware follow-ups

## Tech Stack

- **Backend**: Python 3.8+, FastAPI
- **Notion Integration**: notion-client library
- **Frontend**: HTML/CSS/JavaScript (single-page application)
- **Data Validation**: Pydantic models

## Requirements

See `requirements.txt` for Python dependencies. Main dependencies:
- FastAPI - Web framework
- notion-client - Notion API client
- pydantic - Data validation
- python-dotenv - Environment variable management
