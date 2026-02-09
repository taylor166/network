# Contact Data Model

## Core Contact Fields

### Basic Information
- **id** (unique identifier - Notion page ID if integrated)
- **name** (full name) - *Required*
- **first_name** (for personalization)
- **last_name**

### Contact Information
- **email** (primary email) - *At least one of email or phone required*
- **phone** (primary phone) - *At least one of email or phone required*
- **email_secondary** (alternative email)
- **phone_secondary** (alternative phone)
- **linkedin_url** (for LinkedIn outreach)
- **twitter_handle**
- **website**

### Professional Information
- **title** (job title)
- **company** (current company)
- **industry**
- **location** (city, state/country)
- **company_size** (for potential clients)
- **funding_stage** (for potential clients/startups)

### Status & Workflow (Based on Your Current Notion Structure)

**Status** (single select):
- `wait` - Waiting for something
- `queued` - In queue to contact
- `need_to_contact` - Needs to be contacted
- `contacted` - Initial outreach sent
- `circle_back` - Need to circle back later
- `scheduled` - Meeting scheduled
- `done` - Completed/closed
- `ghosted` - No response after multiple attempts

**Type** (single select):
- `existing` - Existing relationship
- `2026_new` - New contact in 2026
- *Future: Could add `2027_new`, etc.*

**Group** (single select - relationship context):
- `other` - Catch-all
- `fam` - Family
- `McK` - McKinsey (first job)
- `PEA` - Phillips Exeter Academy (high school)
- `GU` - Georgetown University (college)
- `BP` - Berkshire Partners (second job)
- `MBA` - Business school (future)
- `MVNX` - MVNX
- *Future: Could add more groups as needed*

**Relationship Type** (new field - for use case differentiation):
- `friend` - Personal friend
- `advisor` - Advisor/mentor
- `potential_client` - Potential client
- `colleague` - Current/past colleague
- `other` - Other relationship type

### Interaction Tracking (Based on Your Current Structure)

- **last_contact_date** (date of last interaction - email, call, meeting)
- **days_at_current_status** (calculated: days since status changed)
- **call_count** (number of times you've called them)
- **contact_count** (total number of contacts/outreaches)

### Notes & Context
- **notes** (free-form text - your current notes field)
- **source** (where/how you found them: LinkedIn, referral, event, etc.)
- **source_date** (when you found them)
- **source_context** (notes about how/why you found them)
- **mutual_connections** (list of people you both know)
- **common_interests** (topics, industries, etc.)
- **followup_context** (what to mention in next followup)

### Interaction History (Enhanced for Workflows)
- **outreach_history** (array of outreach attempts with dates, templates used, channels, responses)
- **meeting_history** (array of scheduled/held meetings with dates, notes, outcomes)
- **call_history** (array of calls with dates, duration, notes)
- **email_threads** (links to email conversations)
- **linkedin_messages** (links to LinkedIn message threads)

### Follow-up & Automation
- **next_followup_date** (when to follow up next)
- **followup_reminder_set** (boolean - is reminder active?)
- **last_followup_attempt** (date of last follow-up)
- **followup_count** (number of follow-up attempts)

### Metadata
- **created_date** (when contact was added)
- **updated_date** (last modification)
- **archived_date** (if archived)
- **archived_reason** (why they were archived)
- **priority** (high, medium, low - optional for filtering)

## Use Case Considerations

### For Friends
- Focus on: Group, last_contact_date, notes
- Status flow: existing → contacted → scheduled → done
- Less formal outreach, more personal notes

### For Advisors/Mentors
- Focus on: title, company, notes, followup_context
- Status flow: need_to_contact → contacted → scheduled → done
- More structured outreach, track advice given

### For Potential Clients
- Focus on: company, industry, company_size, funding_stage, source
- Status flow: queued → need_to_contact → contacted → scheduled → done
- Track outreach templates, responses, meeting outcomes
- More detailed interaction history

## Data Model Decisions

### Required Fields
- `name` (required)
- `email` OR `phone` (at least one required)
- `status` (required, defaults to "wait" or "queued")
- `created_date` (auto-generated)

### Optional but Recommended
- `type` (existing vs new)
- `group` (relationship context)
- `relationship_type` (friend, advisor, potential_client)
- `last_contact_date`
- `notes`

### Calculated Fields
- `days_at_current_status` (calculated from status change date)
- `days_since_last_contact` (calculated from last_contact_date)

## Questions to Consider

1. **Do you want to track relationship strength/score?** (e.g., 1-10 scale, or tier system)
2. **Should we add more status options?** (e.g., "responded", "meeting_requested")
3. **Do you want tags in addition to groups?** (e.g., "investor", "founder", "potential_customer")
4. **How detailed should call history be?** (just dates, or duration, notes per call?)
5. **Do you want to track email open/click rates?** (if using email tracking)
