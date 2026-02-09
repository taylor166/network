# Contact Management System - Setup Guide

## Overview

This contact management system integrates with Notion as the source of truth. All contacts are stored in your Notion database, and this tool provides a web interface for managing them with enhanced filtering, search, and workflow automation.

## Prerequisites

- Python 3.8 or higher
- A Notion account
- A Notion database with contacts (or we'll help you set one up)

## Step 1: Install Dependencies

### Option A: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** You'll need to activate the virtual environment each time you open a new terminal:
```bash
source venv/bin/activate
```

### Option B: Install Globally

```bash
pip3 install -r requirements.txt
```

**Note:** On macOS, use `python3` and `pip3` instead of `python` and `pip`.

## Step 2: Set Up Notion Integration

### 2.1 Create a Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "+ New integration"
3. Give it a name (e.g., "Contact Management")
4. Select your workspace
5. Under "Capabilities", enable:
   - Read content
   - Update content
   - Insert content
6. Click "Submit" to create the integration
7. Copy the "Internal Integration Token" (starts with `secret_`)

### 2.2 Share Your Database with the Integration

1. Open your Notion contacts database
2. Click the "..." menu in the top right
3. Select "Add connections" or "Connections"
4. Find and select your integration (the one you just created)
5. Click "Confirm"

### 2.3 Get Your Database ID

1. Open your Notion contacts database in a web browser
2. Look at the URL - it will look like:
   ```
   https://www.notion.so/your-workspace/DATABASE_ID?v=...
   ```
3. The Database ID is the long string of characters between the last `/` and the `?`
   - It's typically 32 characters, with dashes
   - Example: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### 2.4 Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```env
   NOTION_API_KEY=secret_your_integration_token_here
   NOTION_DATABASE_ID=your_database_id_here
   HOST=0.0.0.0
   PORT=8000
   ```

## Step 3: Set Up Notion Database Properties

Your Notion database needs to have the following properties. The system will map these to the contact data model:

### Required Properties

- **name** (Title) - The contact's full name
- **email** (Email) - Primary email address
- **phone** (Phone number) - Primary phone number
- **status** (Select) - Contact status with options:
  - `wait`
  - `queued`
  - `need_to_contact`
  - `contacted`
  - `circle_back`
  - `scheduled`
  - `done`
  - `ghosted`

### Recommended Properties

- **type** (Select) - `existing` or `2026_new`
- **group** (Select) - Relationship group: `fam`, `McK`, `PEA`, `GU`, `BP`, `MBA`, `MVNX`, `other`
- **relationship_type** (Select) - `friend`, `advisor`, `potential_client`, `colleague`, `other`
- **title** (Text) - Job title
- **company** (Text) - Company name
- **industry** (Text) - Industry
- **location** (Text) - Location
- **linkedin_url** (URL) - LinkedIn profile URL
- **notes** (Text) - Free-form notes
- **last_contact_date** (Date) - Date of last contact
- **call_count** (Number) - Number of calls
- **days_at_current_status** (Number) - Days at current status
- **created_date** (Date) - When contact was created
- **next_followup_date** (Date) - When to follow up next
- **followup_context** (Text) - Context for next follow-up

### Property Name Mapping

The system expects these exact property names in Notion. If your Notion database uses different names, you have two options:

1. **Rename properties in Notion** to match the expected names (recommended)
2. **Update the mapping** in `contacts/notion_client.py` in the `_map_notion_to_contact` and `_map_contact_to_notion` methods

## Step 4: Run the Application

### If using virtual environment:
```bash
source venv/bin/activate
python main.py
```

### If installed globally:
```bash
python3 main.py
```

The server will start on `http://localhost:8000`

Open your browser and navigate to:
```
http://localhost:8000
```

## Step 5: Verify Connection

1. The application should load the contact management interface
2. If you see "Loading contacts..." that never finishes, check:
   - Your Notion API key is correct
   - Your database ID is correct
   - The integration has access to the database
   - The database has the required properties

You can also test the connection using the health endpoint:
```bash
curl http://localhost:8000/api/health
```

## Troubleshooting

### "Notion API key is required"
- Make sure you've created a `.env` file
- Check that `NOTION_API_KEY` is set correctly
- The key should start with `secret_`

### "Notion database ID is required"
- Make sure `NOTION_DATABASE_ID` is set in your `.env` file
- Verify the database ID is correct (32 characters with dashes)

### "object_not_found" or "database_not_found"
- Make sure you've shared the database with your integration
- Go to your database → "..." menu → "Connections" → Add your integration

### "property_not_found" or missing fields
- Check that your Notion database has all required properties
- Verify property names match exactly (case-sensitive)
- See "Set Up Notion Database Properties" section above

### Contacts not loading
- Check the browser console for errors
- Check the server logs for API errors
- Verify your database has contacts
- Test the API directly: `curl http://localhost:8000/api/contacts`

### CORS errors
- The API is configured to allow all origins in development
- If you're accessing from a different domain, update CORS settings in `contacts/api.py`

## Field Mapping Reference

This table shows how Notion property types map to our data model:

| Data Model Field | Notion Property Type | Notes |
|-----------------|---------------------|-------|
| name | Title | Required |
| email | Email | At least one of email/phone required |
| phone | Phone number | At least one of email/phone required |
| status | Select | Required, must match status options |
| type | Select | Optional |
| group | Select | Optional |
| relationship_type | Select | Optional |
| title | Text | Optional |
| company | Text | Optional |
| industry | Text | Optional |
| location | Text | Optional |
| linkedin_url | URL | Optional |
| notes | Text | Optional |
| last_contact_date | Date | Optional |
| call_count | Number | Optional, defaults to 0 |
| days_at_current_status | Number | Optional, defaults to 0 |
| created_date | Date | Auto-set on create |
| next_followup_date | Date | Optional |
| followup_context | Text | Optional |

## Next Steps

Once the contact management system is working:

1. **Test adding a contact** - Use the "Add Contact" button
2. **Test filtering** - Try different status, type, and group filters
3. **Test search** - Search by name, email, or company
4. **Verify Notion sync** - Check that contacts appear in your Notion database
5. **Build outreach system** - Next component in the workflow

## API Endpoints

- `GET /api/contacts` - List all contacts (with filters)
- `GET /api/contacts/{id}` - Get a single contact
- `POST /api/contacts` - Create a new contact
- `PATCH /api/contacts/{id}` - Update a contact
- `DELETE /api/contacts/{id}` - Delete (archive) a contact
- `GET /api/health` - Health check and connection test

## Support

If you encounter issues:
1. Check the server logs for detailed error messages
2. Verify your Notion integration setup
3. Test the API endpoints directly using curl or Postman
4. Review the field mapping to ensure property names match
