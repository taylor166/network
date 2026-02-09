# Prompt for Next Agent: Build Contact Management with Notion Integration

## Context

I'm building an end-to-end networking/CRM tool. We've designed the architecture and data model, and now need to build the contact management system.

## Architecture Decision: Hybrid Approach with Notion

**Decision:** Use Notion as the source of truth, with this tool providing workflow automation and enhanced UI.

**Approach:**
- Notion database contains all contacts (currently 116 contacts)
- This tool reads/writes to Notion via API
- Notion remains where user views/edits contacts manually
- This tool handles workflows: outreach, scheduling, notes, follow-ups
- Bidirectional sync: changes in either place sync to the other

## Contact Data Model

The contact data model has been designed and is documented in `contacts/templates/contact-data-model.md`. Key fields:

### Core Fields (Based on Current Notion Structure)
- **name** (required)
- **email** OR **phone** (at least one required)
- **status**: wait, queued, need_to_contact, contacted, circle_back, scheduled, done, ghosted
- **type**: existing, 2026_new
- **group**: other, fam, McK, PEA, GU, BP, MBA, MVNX
- **last_contact_date**
- **days_at_current_status** (calculated)
- **call_count** (number of times called)
- **notes** (free-form text)

### Additional Fields Added
- **relationship_type**: friend, advisor, potential_client
- **title**, **company**, **industry**, **location**
- **linkedin_url**
- **outreach_history**, **meeting_history**, **call_history**
- **next_followup_date**, **followup_context**

Full data model is in: `contacts/templates/contact-data-model.md`

## Design Documents

1. **Contact Data Model:** `contacts/templates/contact-data-model.md`
2. **Architecture Decision:** `contacts/templates/architecture-decision.md`
3. **Contact Management Design:** `contacts/contact-management-design.md`
4. **Project Structure:** See `README.md` and `AGENTS.md`

## Your Task: Build Contact Management System

### Requirements

1. **Notion API Integration**
   - Set up Notion API client/connection
   - Map Notion database properties to our contact data model
   - Implement read operations (fetch contacts from Notion)
   - Implement write operations (create/update contacts in Notion)
   - Handle sync conflicts (last-write-wins or manual resolution)
   - Handle rate limiting and API errors gracefully

2. **Contact Management Interface**
   - **Add Contact:** Form to add new contact (writes to Notion)
     - Required: name, email OR phone
     - Optional: all other fields
     - Auto-set: created_date, status defaults
   - **View Contacts:** List/table view with key fields
     - Display: name, contact info, status, type, group, last_contact_date, days_at_current_status, notes
     - Load from Notion
   - **Edit Contact:** Update any field (writes to Notion)
     - Update status, dates, notes, etc.
     - Handle status changes (reset days_at_current_status)
   - **Filter & Search:**
     - Filter by: status, type, group, relationship_type
     - Search by: name, email, phone, company, notes
     - Sort by: last_contact_date, days_at_current_status, name

3. **Status Workflow**
   - Track status transitions
   - Auto-update "days_at_current_status" when status changes
   - Auto-update "last_contact_date" when outreach sent (integration with outreach system)

4. **Integration Points** (Design for these, but don't build yet)
   - Outreach system: Trigger when status is "need_to_contact"
   - Scheduling system: Update status to "scheduled" when meeting scheduled
   - Notes system: Increment call_count
   - Follow-up system: Use next_followup_date for reminders

### Technical Considerations

1. **Notion API Setup**
   - Need Notion integration token
   - Need Notion database ID
   - Map Notion property types to our data model
   - Handle Notion's property naming (may differ from our model)

2. **Data Sync**
   - Read from Notion on load/refresh
   - Write to Notion on create/update
   - Consider caching for performance
   - Handle offline/online state

3. **Error Handling**
   - Notion API rate limits
   - Network errors
   - Invalid data
   - Sync conflicts

4. **Performance**
   - Pagination for large contact lists (116+ contacts)
   - Caching strategy
   - Optimistic UI updates

### Project Context

- This is a networking/CRM tool with end-to-end workflow: source → outreach → schedule → notes → followup
- See `AGENTS.md` for AI assistant instructions (focus on workflows, structure first)
- See `README.md` for project overview
- See `workflows/` for workflow designs (outreach, scheduling, followup)

### Use Cases

The system needs to handle three types of contacts:
1. **Friends** - Personal relationships, less formal
2. **Advisors/Mentors** - Professional relationships, track advice
3. **Potential Clients** - Business relationships, detailed tracking

### Questions to Consider

1. What tech stack should we use? (Python, Node.js, etc.)
2. What UI framework? (Web app, CLI, etc.)
3. How to handle Notion authentication?
4. Should we cache contacts locally or always fetch from Notion?
5. How to handle calculated fields (days_at_current_status)?

### Deliverables

1. Notion API integration layer
2. Contact management interface (add/view/edit)
3. Filtering and search functionality
4. Status workflow management
5. Documentation on how to set up Notion connection
6. Documentation on field mapping between Notion and our data model

### Next Steps After This

Once contact management is built:
- Build outreach system (one-click outreach using templates)
- Build scheduling integration (with existing EA/Scheduler)
- Build notes system
- Build follow-up automation

## Important Notes

- **Don't migrate data** - Keep everything in Notion, just read/write via API
- **Start simple** - Build basic CRUD first, then add filtering/search
- **Design for integration** - Other workflows will need to update contacts
- **Follow project structure** - Use existing folder structure
- **Document as you go** - Update design docs if you make changes

## Files to Reference

- `contacts/templates/contact-data-model.md` - Full data model
- `contacts/templates/architecture-decision.md` - Architecture rationale
- `contacts/contact-management-design.md` - Detailed design
- `AGENTS.md` - AI assistant instructions
- `README.md` - Project overview

---

**Ready to build!** Start with Notion API integration, then build the contact management interface on top of it.
