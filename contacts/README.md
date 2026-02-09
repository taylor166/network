# Contact Management System

Contact management system with Notion integration for the networking/CRM tool.

## Quick Start

1. **Set up Notion integration** (see `SETUP.md` for detailed instructions):
   - Create a Notion integration at https://www.notion.so/my-integrations
   - Get your integration token and database ID
   - Add credentials to `.env` file

2. **Install dependencies**:
   ```bash
   # Create and activate virtual environment (recommended)
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # OR install globally
   pip3 install -r requirements.txt
   ```

3. **Run the server**:
   ```bash
   # If using virtual environment, activate it first:
   source venv/bin/activate
   
   # Then run:
   python main.py
   
   # OR if installed globally:
   python3 main.py
   ```

4. **Open in browser**:
   ```
   http://localhost:8000
   ```

## Features

- ✅ **Notion Integration** - Bidirectional sync with Notion database
- ✅ **Add Contacts** - Create new contacts with validation
- ✅ **View Contacts** - List all contacts in a table view
- ✅ **Edit Contacts** - Update any contact field
- ✅ **Filter & Search** - Filter by status, type, group, relationship type; search by name, email, company
- ✅ **Status Workflow** - Track contact status with auto-updates
- ✅ **Sorting** - Sort by name, last contact date, days at status

## Architecture

- **`notion_client.py`** - Notion API client with read/write operations
- **`models.py`** - Pydantic models for data validation
- **`api.py`** - FastAPI endpoints for contact management
- **`static/index.html`** - Frontend UI (single-page application)

## Data Model

See `templates/contact-data-model.md` for the complete data model specification.

### Required Fields
- `name` (required)
- `email` OR `phone` (at least one required)
- `status` (defaults to "queued")

### Key Fields
- Status: wait, queued, need_to_contact, contacted, circle_back, scheduled, done, ghosted
- Type: existing, 2026_new
- Group: fam, Ext, Gtn, Mck, BP, MBA, other
- Relationship Type: friend, advisor, potential_client, colleague, other

## API Endpoints

- `GET /api/contacts` - List contacts (with query params for filtering)
- `GET /api/contacts/{id}` - Get single contact
- `POST /api/contacts` - Create contact
- `PATCH /api/contacts/{id}` - Update contact
- `DELETE /api/contacts/{id}` - Delete (archive) contact
- `GET /api/health` - Health check

## Status Workflow

When a contact's status changes:
- `days_at_current_status` is automatically reset to 0
- Status transitions are tracked for workflow automation

## Integration Points

This system is designed to integrate with:
- **Outreach System** - Update status when outreach sent
- **Scheduling System** - Update status to "scheduled" when meeting scheduled
- **Notes System** - Increment call_count
- **Follow-up System** - Use next_followup_date for reminders

## Configuration

Environment variables (in `.env`):
- `NOTION_API_KEY` - Notion integration token
- `NOTION_DATABASE_ID` - Notion database ID
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)

## Documentation

- **Setup Guide**: `SETUP.md` - Detailed setup instructions
- **Data Model**: `templates/contact-data-model.md` - Complete field specifications
- **Architecture**: `templates/architecture-decision.md` - Design decisions
- **Design**: `contact-management-design.md` - System design document

## Troubleshooting

See `SETUP.md` for troubleshooting common issues.

Common issues:
- Notion API key not set
- Database not shared with integration
- Property names don't match expected names
- CORS errors (check API configuration)
