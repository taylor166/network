# Contact Management System Design

## Overview

Contact management is the foundation of the networking/CRM tool. It handles creating, viewing, editing, and organizing contacts across three primary use cases: friends, advisors/mentors, and potential clients.

## Core Functionality

### 1. Add Contact
- **Input fields:**
  - Name (required)
  - Email OR Phone (at least one required)
  - Optional: Title, Company, LinkedIn, Notes
  - Status (defaults based on context)
  - Type (existing or new)
  - Group (relationship context)
  - Relationship Type (friend, advisor, potential_client)
- **Auto-populate:**
  - Created date
  - Status (default: "queued" or "wait")
  - Days at current status (starts at 0)
- **Quick add:** Minimal fields for speed
- **Full add:** All fields available

### 2. View Contacts
- **List view:** Table/grid with key fields
  - Name, Contact Info (email/phone), Status, Type, Group, Last Contact Date, Days at Status, Notes
- **Filtering:**
  - By status (wait, queued, need_to_contact, contacted, circle_back, scheduled, done, ghosted)
  - By type (existing, 2026_new)
  - By group (fam, Ext, Gtn, Mck, BP, MBA, other)
  - By relationship type (friend, advisor, potential_client)
  - By days since last contact
  - By call count
- **Sorting:**
  - Last contact date (newest/oldest)
  - Days at current status
  - Name (alphabetical)
  - Created date
- **Search:**
  - By name, email, phone, company, notes

### 3. Edit Contact
- **Update any field:**
  - Basic info, contact info, professional info
  - Status, Type, Group, Relationship Type
  - Notes
- **Update interaction dates:**
  - Last contact date (auto-updates when outreach sent)
- **Increment counters:**
  - Call count (when call logged)
  - Contact count (when outreach sent)
- **Status changes:**
  - When status changes, reset "days at current status" counter
  - Update "last contact date" if status change represents contact

### 4. Contact Details View
- **Full contact information**
- **Interaction history:**
  - Outreach history (with dates, templates, responses)
  - Meeting history (with dates, notes, outcomes)
  - Call history (with dates, notes)
- **Notes timeline:**
  - Chronological notes with dates
- **Quick actions:**
  - Send outreach (one-click)
  - Schedule meeting
  - Log call
  - Add note
  - Set follow-up reminder

## Status Workflow

### Status Transitions

```
wait → queued → need_to_contact → contacted → [scheduled | circle_back | done | ghosted]
                                                      ↓
                                                   done
```

**Status Meanings:**
- `wait` - Waiting for something (e.g., waiting for them to reach out)
- `queued` - In queue, ready to contact
- `need_to_contact` - Needs to be contacted (actionable)
- `contacted` - Initial outreach sent
- `circle_back` - Need to follow up later (not now)
- `scheduled` - Meeting scheduled
- `done` - Completed/closed (met, helped, etc.)
- `ghosted` - No response after multiple attempts

**Auto-status updates:**
- When outreach sent → status becomes "contacted" (if was "need_to_contact")
- When meeting scheduled → status becomes "scheduled"
- When meeting completed → status becomes "done" (or stays "scheduled" if more meetings)
- After N days with no response → suggest "ghosted" or "circle_back"

## Use Case Specific Features

### For Friends
- **Quick add:** Name + phone/email + group
- **Focus fields:** Group, last_contact_date, notes
- **Status flow:** Usually existing → contacted → scheduled → done
- **Less formal:** Shorter notes, more personal context

### For Advisors/Mentors
- **Full add:** Name + email + title + company + notes
- **Focus fields:** Title, company, notes, followup_context
- **Status flow:** need_to_contact → contacted → scheduled → done
- **Track advice:** Notes should capture advice given, topics discussed

### For Potential Clients
- **Full add:** All professional fields
- **Focus fields:** Company, industry, company_size, source, outreach_history
- **Status flow:** queued → need_to_contact → contacted → scheduled → done
- **Track outreach:** Detailed outreach history, response tracking, meeting outcomes

## Integration Points

### With Notion (if hybrid approach)
- **Read:** Pull contacts from Notion database
- **Write:** Update Notion when contacts change
- **Sync:** Handle conflicts (last-write-wins or manual resolution)
- **Fields mapping:** Map Notion properties to our data model

### With Outreach System
- **Trigger:** When contact status is "need_to_contact" → show in outreach queue
- **Update:** After outreach sent → update status to "contacted", update last_contact_date, add to outreach_history

### With Scheduling System
- **Trigger:** When positive response → move to scheduling workflow
- **Update:** When meeting scheduled → update status to "scheduled", add to meeting_history

### With Notes System
- **Link:** Notes associated with contact
- **Update:** When call note added → increment call_count

### With Follow-up System
- **Trigger:** Contacts with follow-up dates → show in follow-up queue
- **Update:** After follow-up sent → update last_contact_date, increment followup_count

## Data Calculations

### Days at Current Status
- Calculated: Current date - status_change_date
- Auto-update daily or on-demand
- Reset to 0 when status changes

### Days Since Last Contact
- Calculated: Current date - last_contact_date
- Used for follow-up prioritization

### Contact Frequency Score (optional)
- Based on: last_contact_date, call_count, meeting_count
- Helps prioritize who to reach out to

## Views & Filters

### Default Views
1. **Action Queue** - Status: need_to_contact, queued
2. **Follow-ups Needed** - next_followup_date <= today
3. **Recently Contacted** - last_contact_date in last 7 days
4. **Scheduled Meetings** - Status: scheduled
5. **Circle Back** - Status: circle_back, sorted by date

### Custom Filters
- By group (e.g., all McKinsey contacts)
- By relationship type (e.g., all advisors)
- By days since contact (e.g., >30 days)
- By status (e.g., all "contacted" waiting for response)

## Bulk Operations

- **Bulk status update:** Change status for multiple contacts
- **Bulk tag/group:** Assign group to multiple contacts
- **Bulk export:** Export filtered contacts to CSV
- **Bulk import:** Import contacts from CSV (with field mapping)

## Questions to Answer

1. **Do you want a "favorites" or "starred" feature?** (Quick access to important contacts)
2. **Should we add contact merging?** (If duplicate contacts found)
3. **Do you want contact archiving?** (Move to archived folder vs. delete)
4. **How should we handle contact de-duplication?** (By email? By phone? By name+company?)
5. **Do you want contact sharing/export?** (Share with team, export for backup)
