# Outreach Workflow Design

## Workflow Stages

### 1. Source & Add Contact
- Find contact through various channels (LinkedIn, events, referrals)
- Add to system with source information
- Tag and categorize appropriately
- **Status:** `new`

### 2. Prepare Outreach
- Review contact information and context
- Select appropriate template
- Personalize template with contact-specific details
- **Status:** `prepared` or `ready_to_contact`

### 3. Send Outreach
- One-click send (using template + personalization)
- Track sent date/time
- Record template used
- **Status:** `contacted`
- **Outreach History:** Add entry with date, template, channel

### 4. Wait for Response
- Monitor for responses
- Track response time
- **Status:** `awaiting_response`

### 5. Handle Response
- **If positive response:**
  - Move to scheduling workflow
  - **Status:** `responded` → `scheduling`
- **If no response:**
  - Set follow-up reminder
  - **Status:** `no_response` → `followup_needed`

### 6. Follow-up (if needed)
- Automated reminder based on time since last outreach
- Use follow-up template
- Track follow-up attempts
- **Status:** `followup_sent`

## Data Flow

```
Contact Created
    ↓
Source Info Captured
    ↓
Template Selected & Personalized
    ↓
Outreach Sent → Recorded in History
    ↓
Response Received? 
    ├─ Yes → Scheduling Workflow
    └─ No → Follow-up Workflow
```

## Integration Points

- **Email Integration:** Send emails, receive responses
- **LinkedIn Integration:** Send LinkedIn messages, track responses
- **Scheduling Integration:** When positive response, trigger EA/Scheduler
- **Follow-up System:** Automated reminders based on context

## Questions to Consider

1. **How long do you wait before following up?** (e.g., 3 days, 1 week)
2. **How many follow-up attempts?** (e.g., 2-3 max)
3. **What triggers a move to "archived"?** (e.g., 3 no-responses, explicit decline)
4. **How do you prioritize who to reach out to?** (e.g., by source, by priority tag, by date added)
