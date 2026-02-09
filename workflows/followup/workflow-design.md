# Follow-up Workflow Design

## Context-Aware Follow-ups

Follow-ups should be based on:
- Previous interaction history
- Time since last contact
- Contact status and stage
- Specific context from notes or previous conversations

## Workflow Stages

### 1. Follow-up Triggers

**Automatic Triggers:**
- No response after X days (e.g., 3-7 days)
- Post-meeting follow-up (e.g., 1-2 days after meeting)
- Scheduled follow-up date reached
- Milestone-based (e.g., after they share something relevant)

**Manual Triggers:**
- User-initiated follow-up
- Context-based reminder (e.g., "Follow up about X in 2 weeks")

### 2. Determine Follow-up Type

**Types:**
- **Re-engagement:** No response to initial outreach
- **Thank you:** After a meeting
- **Value-add:** Share relevant resource/article
- **Check-in:** Periodic relationship maintenance
- **Contextual:** Based on specific conversation topic

### 3. Select Template & Personalize

- Choose appropriate follow-up template
- Personalize with:
  - Previous interaction context
  - Notes from last conversation
  - Specific topics discussed
  - Mutual interests or connections

### 4. Send Follow-up

- One-click send (using template + personalization)
- Track sent date/time
- Record in interaction history
- **Status:** Updated based on follow-up type

### 5. Track Results

- Monitor for response
- Update contact status
- Set next follow-up date if needed
- **If no response after N attempts:** Consider archiving

## Follow-up Rules

### Re-engagement (No Response)
- **Timing:** 3-7 days after initial outreach
- **Max Attempts:** 2-3
- **After Max Attempts:** Move to "low priority" or archive

### Post-Meeting
- **Timing:** 1-2 days after meeting
- **Type:** Thank you + next steps
- **Always send:** Yes (unless explicitly not needed)

### Value-add Follow-up
- **Timing:** When relevant content/opportunity arises
- **Type:** Share resource, introduce to someone, etc.
- **Context-driven:** Based on conversation topics

### Periodic Check-in
- **Timing:** Every 30-90 days for active relationships
- **Type:** Light touch, relationship maintenance
- **Priority:** Based on relationship strength

## Data Flow

```
Follow-up Trigger
    ↓
Determine Type & Context
    ↓
Select Template
    ↓
Personalize with Context
    ↓
Send Follow-up
    ↓
Track Response
    ↓
Update Status & Set Next Follow-up
```

## Integration Points

- **Contact History:** Access previous interactions
- **Notes System:** Use meeting notes for context
- **Templates:** Follow-up email/message templates
- **Email/LinkedIn:** Send follow-up messages
- **Analytics:** Track follow-up effectiveness

## Questions to Consider

1. **What's your follow-up cadence?** (e.g., 3 days, 1 week, 2 weeks)
2. **How do you decide when to stop following up?** (e.g., 3 attempts, explicit decline)
3. **What makes a follow-up "contextual"?** (e.g., based on notes, shared interests, timing)
4. **How do you prioritize follow-ups?** (e.g., by relationship strength, by time since last contact)
