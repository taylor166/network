# Scheduling Workflow Design

## Integration with EA/Scheduler

This workflow integrates with your existing EA/Scheduler project that:
- Takes inputs from emails
- Offers available times based on Google Calendar
- Considers timing preferences
- Schedules meetings

## Workflow Stages

### 1. Positive Response Received
- Contact responds positively to outreach
- **Status:** `responded`
- **Trigger:** Move to scheduling workflow

### 2. Initiate Scheduling
- Extract meeting request from response
- Determine meeting type (e.g., 15-min intro, 30-min deep dive)
- **Status:** `scheduling`

### 3. EA/Scheduler Integration
- Pass contact info and meeting context to EA/Scheduler
- EA/Scheduler:
  - Checks Google Calendar for availability
  - Considers timing preferences
  - Generates available time slots
  - Sends options to contact

### 4. Meeting Confirmed
- Contact selects a time slot
- Meeting is scheduled in Google Calendar
- **Status:** `scheduled`
- **Meeting History:** Add entry with date, time, type

### 5. Pre-Meeting Preparation
- Set reminder (e.g., 1 day before)
- Prepare context (review notes, previous interactions)
- **Status:** `scheduled` (with upcoming meeting date)

### 6. Post-Meeting
- Move to notes workflow
- **Status:** `met`
- **Trigger:** Notes workflow

## Data Flow

```
Positive Response
    ↓
Extract Meeting Request
    ↓
EA/Scheduler Integration
    ├─ Check Calendar Availability
    ├─ Generate Time Slots
    └─ Send to Contact
    ↓
Meeting Confirmed
    ↓
Scheduled in Calendar
    ↓
Pre-Meeting Prep
    ↓
Meeting Held → Notes Workflow
```

## Integration Points

- **EA/Scheduler:** Core scheduling logic
- **Google Calendar:** Availability checking and event creation
- **Email:** Receive responses, send scheduling options
- **Notes System:** Post-meeting note-taking

## Questions to Consider

1. **What meeting types do you typically schedule?** (e.g., intro calls, deep dives, coffee chats)
2. **How do you handle rescheduling?** (e.g., automatic re-trigger of EA/Scheduler)
3. **What context should be passed to EA/Scheduler?** (e.g., contact name, meeting type, duration)
4. **How do you handle no-shows?** (e.g., automatic follow-up, reschedule option)
