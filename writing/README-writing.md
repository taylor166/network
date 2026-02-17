# Outreach Prompt System Setup Guide

## File Structure

Drop these files into your Cursor project directory (e.g., `/prompts/` or `/context/`):

```
prompts/
  01_SYSTEM_PROMPT.md    | Core instructions and rules
  02_VOICE_GUIDE.md      | How Taylor writes (tone, word choice, patterns)
  03_CATEGORY_PLAYBOOKS.md | Strategic approach for each outreach type
  04_CONTEXT_SCHEMA.md   | Data fields and how to use them
  05_ANTI_PATTERNS.md    | What NOT to do (the kill list)
  06_GOLD_EXAMPLES.md    | Calibrated examples of great output
  07_BATCH_TRACKER.md    | Live variation tracking for batches
```

## How to Use in Cursor

### Option A: Reference as context files
In your Cursor agent/prompt, include these as context references:
```
@prompts/01_SYSTEM_PROMPT.md
@prompts/02_VOICE_GUIDE.md
@prompts/03_CATEGORY_PLAYBOOKS.md
... etc
```

### Option B: Paste the System Prompt as a custom instruction
Copy the contents of `01_SYSTEM_PROMPT.md` into Cursor's system prompt / custom instructions field. Then reference the other files as needed context.

### Option C: Build into your Agent 3 pipeline
If you're using the agent pipeline (call processing enrichment email draft battle card), these files replace the current outreach template and become the reference library for Agent 3.

## What Changed vs. Your Old Template

| Old System | New System |
|-----------|-----------|
| 2 email templates (cold intro, reconnect) | 6 categories with 3-4 structural variations each |
| Fixed structure per template | Flexible structures that rotate |
| Variable swapping on fixed sentences | Sentence-level rewriting for each contact |
| Same CTA every time | CTA rotation with tracking |
| Same subject line pattern | Subject line variation with tracking |
| "Saw your path from X to Y" everywhere | 7+ opening move options |
| "Vibe check" in every cold email | Max 1 per 10 messages |
| No batch awareness | Batch tracker prevents pattern repetition |
| Personalization = swapping variables | Personalization = restructuring the entire message around the contact's data |

## Iterating on This System

After you've sent 20-30 messages with this system:

1. **Track response rates by category.** Which playbook variations get the most replies?
2. **Save your best-performing messages** and add them to `06_GOLD_EXAMPLES.md`.
3. **Add new anti-patterns** to `05_ANTI_PATTERNS.md` as you notice them.
4. **Update the Voice Guide** if your writing style evolves (e.g., as you transition from Berkshire to Stanford, your self-intro will change).
5. **Add new categories** to the playbook as new outreach types emerge (e.g., Stanford classmate intros, investor outreach for Mavnox, etc.).

## Quick Test

To verify the system is working, give it the same contact info 3 times and ask for 3 different drafts. If all 3 look meaningfully different in structure, opening, and CTA, it's calibrated correctly. If they look similar, the anti-pattern checking isn't being applied properly.