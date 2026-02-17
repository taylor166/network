# Context Schema

This document defines every data field the system may receive for a contact and how to use (or not use) each one in drafting.

---

## CONTACT DATA FIELDS

### Identity Fields

| Field | Description | How to Use |
|-------|-------------|------------|
| `first_name` | Contact's first name | Always use in greeting. Never use last name in greeting unless the tone is deliberately formal (rare). |
| `last_name` | Contact's last name | Use only in subject lines or forwardable blurbs. |
| `email` | Contact's email address | Channel selection only. Never reference in body. |
| `phone` | Contact's phone number | Channel selection only. Never reference in body. |

### Relationship Fields

| Field | Description | How to Use |
|-------|-------------|------------|
| `type` | "existing" or "2026_new" | **Critical.** Determines whether to use reconnect or cold intro playbook. Existing = they know who Taylor is. 2026_new = they don't. |
| `status` | Contact status | If "existing," always apply the Update-First logic (include personal update before ask). |
| `group` | Shared affiliation | **Critical.** PEA = Exeter, McK = McKinsey, GU = Georgetown, BP = Berkshire Partners, MBA = business school, MVNX = Mavnox, fam = family. If "Other" or blank, do NOT reference a shared network. |
| `group_name` | Full name of the group | Use this instead of the abbreviation in the message. "McKinsey" not "McK." |
| `last_contact_date` | Date of last interaction | Use to calibrate tone. Recent = casual continuation. Old = acknowledge time gap (but don't be dramatic about it). |
| `relationship_warmth` | close / warm / cool / cold | Maps directly to the tone calibration in the Voice Guide. This is the most important tone-setting field. |

### Professional Fields

| Field | Description | How to Use |
|-------|-------------|------------|
| `company` | Current company | Reference naturally. Don't always put it in the same position. Sometimes in the hook, sometimes in the interest expression, sometimes not at all. |
| `current_role` | Current job title | Use sparingly. Titles are less interesting than what they actually DO. "Your work building [thing]" > "In your role as VP of Engineering." |
| `previous_company` | Prior company | Useful for the "path from X to Y" hook, but DON'T overuse this pattern. It's one option among many. |
| `previous_role` | Prior job title | Same as above. |
| `industry` | Industry sector | Use for cold outreach when no shared network exists. Also useful for framing your ask: "your experience in [industry]." |
| `career_path_type` | operator / investor / founder | Subtly informs word choice. Operators respond to operational language. Investors respond to thesis/market language. Founders respond to builder language. |

### Context Fields

| Field | Description | How to Use |
|-------|-------------|------------|
| `location` | City/region | Use in texts for warm contacts ("Hope [City] is treating you well"). For emails, use only if geographically relevant to the ask. Don't shoehorn it in. |
| `notes` | CRM notes from prior interactions | **HIGH VALUE.** If notes exist, use them to personalize beyond template. Reference specific things discussed, commitments made, or topics of mutual interest. |
| `prior_interactions` | Summary of past contact | Use to avoid repeating yourself. If you already pitched Stanford in a previous email, don't lead with it again. Reference what you discussed, not your bio. |
| `linkedin_url` | LinkedIn profile URL | Research reference only. Never say "I saw on your LinkedIn." |
| `recent_activity` | Recent posts, news, job changes | **HIGH VALUE for cold outreach.** A specific reference to something they recently did is 10x more compelling than a generic template. |
| `mutual_connections` | Shared contacts | Can use to establish credibility: "I know [mutual] through [context]." But don't name-drop without purpose. |

### Outreach Metadata

| Field | Description | How to Use |
|-------|-------------|------------|
| `outreach_goal` | What Taylor wants from this interaction | Informs the CTA. "Get a call" vs. "Get an intro" vs. "Share a resource" vs. "Nurture the relationship." |
| `topic` | Specific topic Taylor wants to discuss | Use to make the ask specific. "Talk about AI in field services" > "catch up." |
| `batch_id` | Which outreach batch this belongs to | **ANTI-PATTERN DETECTION.** If multiple contacts share the same batch_id, vary structure and language MORE aggressively between them. Assume they might compare notes. |
| `channel` | email or text | Determined by channel selection rules. Dictates format, length, tone, and CTA style. |

---

## FIELD PRIORITY FOR PERSONALIZATION

When multiple data points are available, prioritize what makes the message feel most individually written:

**Tier 1 â€” Use these first (highest personalization impact):**
- `notes` (prior conversation content)
- `recent_activity` (something they just did)
- `mutual_connections` (shared people)
- `prior_interactions` (conversation history)

**Tier 2 â€” Strong personalization:**
- `company` + what they specifically do there
- Career transition story (previous â†’ current)
- `topic` (specific shared interest)

**Tier 3 â€” Basic personalization (minimum bar):**
- `group` / `group_name` (shared network)
- `industry`
- `location`
- `current_role`

**Rule:** Never draft a message that only uses Tier 3 fields. If you only have Tier 3 data, the message must compensate with stronger voice and more creative structure. A Tier-3-only message with a template structure = the current failure mode.

---

## WHAT TO DO WHEN DATA IS SPARSE

Sometimes you'll get a contact with barely any data â€” just a name, email, and maybe a group.

**Do NOT fill the gaps with generic language.** Instead:

1. Keep the message shorter. Less data = shorter message.
2. Lead with your strongest available hook (even if it's just the shared network).
3. Make the ask itself do the personalizing: "I'm curious about [specific question]" is personal even without data about them.
4. If you truly have nothing, write a 2-sentence message. Brevity > fake personalization.

**Example of sparse-data done well:**
```
Hi [Name] -

I'm a fellow Exeter alum, currently working at Berkshire Partners. I'm building something in the AI space and would value a quick conversation.

Any chance you'd have some time in the next few days for a quick call? I'd love to connect and get your input.

Best,
Taylor
```

This works because it's honest about what it is: a network-based cold outreach - and doesn't pretend to know more than it does.