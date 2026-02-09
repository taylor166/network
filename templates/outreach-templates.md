# Outreach Templates

## OUTREACH CHANNEL RULES

1. **If phone number exists → DEFAULT TO TEXT.**
2. **If no phone but email exists → USE EMAIL.**
3. **If both exist → TEXT FIRST.**
4. **If neither exists → attempt to source email; email is fallback.**

---

## VOICE GUIDELINES

- Write like a peer, never like a student.
- Avoid fluff, praise, or overly formal language.
- Keep messages efficient and natural.
- Establish relevance quickly.
- Make low-friction asks (quick call, brief chat).
- Keep subject lines of emails direct.
- **No emojis ever. No emdash ever.**
- Concise is better.

---

## CRITICAL COMPOSITION RULES

### 1. The "Once-Only" Rule
**Instruction:** Never use the same key noun or phrase (e.g., 'next chapter', 'transition', 'reconnect') more than once in the same message. If you find a duplicate, use a synonym or delete the sentence.

**Examples of duplicates to avoid:**
- Using "transition" twice → use "shift" or "move" for the second instance
- Using "reconnect" twice → use "catch up" or "touch base" for the second instance
- Using "perspective" twice → use "take" or "view" for the second instance

### 2. The "Update-First" Logic (For Existing Contacts)
**Instruction:** When Status is "existing" OR Type is "existing", always include a one-sentence personal update before the ask.

**Current Update:** "Heading to Stanford for business school this fall."

**Format:** Place the update immediately after the greeting and before any context or ask.

### 3. The "Group Name" Safety Filter
**Instruction:** If the Group field is 'Other' or blank, do not reference a network. Instead, use: "I came across your background while researching [Industry]."

**When Group is valid (PEA, McK, GU, BP, MBA, MVNX, fam):**
- Reference the network: "through the {{Group Name}} network" or "via {{Group Name}}"

**When Group is 'Other' or blank:**
- Use: "I came across your background while researching {{Industry}}."

### 4. The "Call-to-Action" (CTA) Standard
**Instruction:** 
- **Email:** Use: "Would you have 15 minutes for a brief 'vibe check' on [Topic]?" OR "You free for a brief call next week?"
- **Text:** Use: "Let me know if you're free for a quick call in the coming days, looking forward to it!" OR "Would you be open to a 10-minute call in the coming weeks?"

**Never mix email and text CTAs.**

---

## TEMPLATE TYPE SELECTION

### Cold Intro (Formal)
- Use when: **Type = "2026 new"** AND **no last contact date** (assume you've never met)

### Reconnect (Casual)
- Use when: **Type = "existing"** OR **has last contact date** (assume they know who you are)

---

## EMAIL TEMPLATES

### Email - Cold Intro

**Subject:** {{Group Name}} / {{Topic}} (e.g., "Exeter / Starting Businesses" or "McKinsey / AI Consulting")

**Body:**
```
Hi {{First Name}} – 

Saw your path from {{Previous Company/Role}} to {{Current Company/Role}}. I'm a {{Group Name}} alum {{one-line identity: e.g., heading to Stanford for my MBA this fall}} and I'm currently focused on {{current focus: e.g., building AI automation consulting}}.

Would love to get your "vibe check" on {{topic: e.g., making that jump into entrepreneurship}}. Do you have 15 mins this month?

Best,
Taylor
```

**Alternative (when Group is 'Other' or blank):**
```
Hi {{First Name}} – 

I came across your background while researching {{Industry}} and saw your path from {{Previous Company/Role}} to {{Current Company/Role}}. I'm currently {{one-line identity}} and I'm focused on {{current focus}}.

Would love to get your "vibe check" on {{topic}}. Do you have 15 mins this month?

Best,
Taylor
```

### Email - Reconnect

**Subject:** Catching up / {{Update Topic}} (e.g., "Catching up / Stanford update")

**Body:**
```
Hi {{First Name}} – 

It's been a while! Wanted to share a quick update that {{personal update: e.g., I'm heading to Stanford for business school later this year}}.

Before I head out, I'd love to hear how things are at {{Company}} and get your pulse on the {{Industry}} space. You free for a brief call next week?

Best,
Taylor
```

---

## TEXT TEMPLATES

### Text - Cold Intro

```
Hi {{First Name}}, this is Taylor Walshe. We haven't met, but I've been following your work in {{Industry}}. I'd love to get your perspective on {{topic: e.g., developing AI capability}}. Would you be open to a 10-minute call in the coming weeks?
```

### Text - Reconnect

```
{{First Name}}! Hope {{Location}} is treating you well. Been too long—would love to catch up and hear what you've been up to. Let me know if you're free for a quick call in the coming days, looking forward to it!
```

---

## PERSONALIZATION REQUIREMENTS

**Every outreach message MUST feel individually written.**

Use available profile data to customize the message while preserving the default structure and following all composition rules.

### Primary Fields to Pull From

- **Company**
- **Current role**
- **Prior roles**
- **Group** (PEA, McK, GU, BP, MBA, MVNX, fam, other) - **Critical for network reference**
- **Location / geography**
- **Notes from CRM**
- **Prior interactions**
- **Industry**
- **Career transitions**
- **Type** (existing vs 2026_new) - **Critical for update-first logic**
- **Status** - **Critical for update-first logic**
- **Operator vs investor vs founder path**
- **Any unique or distinguishing detail**

### Personalization Priority Order

If multiple data points exist, prioritize relevance in this order:

1. **Group** (for network reference - check safety filter first)
2. **Type/Status** (for update-first logic if existing)
3. **Current role or company**
4. **Career move or transition**
5. **Industry overlap**
6. **Geography**
7. **Notes / prior conversations**

### Personalization Checklist

Before sending, verify:
- [ ] **Once-Only Rule:** No duplicate key nouns/phrases
- [ ] **Update-First:** If existing contact, personal update included
- [ ] **Group Safety:** Network reference only if Group is valid (not 'Other' or blank)
- [ ] **CTA Match:** Email CTA for email, Text CTA for text
- [ ] **Subject Line:** Includes Group name and topic (for cold intro emails)

---

## TEMPLATE VARIABLES

### Standard Variables
- `{{First Name}}` - Contact's first name
- `{{Company}}` - Current company
- `{{Current role}}` - Current job title/role
- `{{Location}}` - Geographic location
- `{{Industry}}` - Industry sector
- `{{Previous Company/Role}}` - Prior company or role (for career path references)

### Connection Variables
- `{{Group Name}}` - Shared group (PEA, McK, GU, BP, MBA, MVNX, fam) - **Only use if Group is not 'Other' or blank**
- `{{one-line identity}}` - Brief description of who you are (e.g., "heading to Stanford for my MBA this fall")
- `{{current focus}}` - What you're currently working on (e.g., "building AI automation consulting")

### Personalization Variables
- `{{topic}}` - The topic you want to discuss (e.g., "making that jump into entrepreneurship", "developing AI capability")
- `{{personal update}}` - Personal update for existing contacts (e.g., "I'm heading to Stanford for business school later this year")

### Dynamic Variables (Based on Contact Data)
- `{{Group Name}}` - Maps to: PEA → "Exeter", McK → "McKinsey", GU → "Georgetown", BP → "Berkshire Partners", MBA → "business school", MVNX → "MVNX", fam → "family"
- `{{Network Reference}}` - Either "through the {{Group Name}} network" OR "I came across your background while researching {{Industry}}" (based on Group safety filter)

---

## MASTER TEMPLATE EXAMPLES

### Scenario #1: Cold Intro (Email)
**Subject:** Exeter / Starting Businesses

**Body:**
```
Hi {{First Name}} – 

Saw your path from Cornerstone to founding your own ventures. I'm an Exeter alum heading to Stanford for my MBA this fall and I'm currently focused on building AI automation consulting.

Would love to get your "vibe check" on making that jump into entrepreneurship. Do you have 15 mins this month?

Best,
Taylor
```

### Scenario #2: Reconnect (Email)
**Subject:** Catching up / Stanford update

**Body:**
```
Hi {{First Name}} – 

It's been a while! Wanted to share a quick update that I'm heading to Stanford for business school later this year.

Before I head out, I'd love to hear how things are at {{Company}} and get your pulse on the {{Industry}} space. You free for a brief call next week?

Best,
Taylor
```

### Scenario #3: Reconnect (Text)
```
{{First Name}}! Hope LA is treating you well. Been too long—would love to catch up and hear what you've been up to. Let me know if you're free for a quick call in the coming days, looking forward to it!
```

### Scenario #4: Cold Intro (Text)
```
Hi {{First Name}}, this is Taylor Walshe. We haven't met, but I've been following your work in {{Industry}}. I'd love to get your perspective on developing AI capability. Would you be open to a 10-minute call in the coming weeks?
```

---

## USAGE NOTES

- **Always personalize** - Never send a template without customization
- **Match tone to relationship** - Cold intro for new contacts, reconnect for existing
- **Keep it brief** - Respect their time
- **Make the ask clear** - What do you want? (call, chat, perspective)
- **Follow all composition rules** - Once-Only, Update-First, Group Safety, CTA Standard
- **Verify before sending** - Use the personalization checklist
