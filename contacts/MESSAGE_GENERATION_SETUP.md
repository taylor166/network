# Message Generation Setup

The message generation system uses AI (Anthropic Claude) to create highly customized and human messages based on the markdown files in the `writing/` folder.

## Prerequisites

1. **Anthropic API Key**: You need an Anthropic API key to use this feature.

## Setup Steps

### 1. Install Dependencies

The OpenAI SDK has been added to `requirements.txt`. Install it:

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variable

Add your Anthropic API key to your `.env` file:

```bash
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

Or export it in your shell:

```bash
export ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

### 3. Verify Writing Guide Files

Ensure all markdown files are present in the `writing/` folder:

- `00_CURRENT_CONTEXT.md` - Taylor's current professional status
- `01_SYSTEM_PROMPT.md` - Core instructions and rules
- `02_VOICE_GUIDE.md` - How Taylor writes (tone, word choice, patterns)
- `03_CATEGORY_GUIDE.md` - Strategic approach for each outreach type
- `04_CONTEXT_SCHEMA.md` - Data fields and how to use them
- `05_ANTI_PATTERNS.md` - What NOT to do (the kill list)
- `06_GOLD_EXAMPLES.md` - Calibrated examples of great output

### 4. Restart the Backend Server

After setting the environment variable, restart your FastAPI server:

```bash
uvicorn contacts.api:app --reload
```

## How It Works

1. **Frontend Request**: When you click to generate a draft, the frontend calls `/api/messages/generate-draft`
2. **Context Loading**: The backend loads all markdown files from `writing/` folder
3. **AI Generation**: The system sends the contact data and writing guides to Anthropic Claude
4. **Draft Return**: A personalized message is generated following all the guidelines

## API Endpoint

### POST `/api/messages/generate-draft`

**Request Body:**
```json
{
  "contact_id": "notion-page-id",
  "batch_id": "optional-batch-id",
  "recent_draft_ids": ["optional", "draft", "ids"]
}
```

**Response:**
```json
{
  "subject": "Email subject (empty for texts)",
  "body": "Message body",
  "channel": "email" or "text"
}
```

## Troubleshooting

### Error: "Message generation not configured"

- Check that `ANTHROPIC_API_KEY` is set in your environment
- Verify the environment variable is loaded (restart the server after setting it)

### Error: "Writing guide file not found"

- Ensure all markdown files exist in the `writing/` folder
- Check file names match exactly (case-sensitive)

### Drafts don't match Taylor's voice

- Review the markdown files in `writing/` folder
- Update `00_CURRENT_CONTEXT.md` with current status
- Check `02_VOICE_GUIDE.md` for voice guidelines
- Review `05_ANTI_PATTERNS.md` to ensure patterns aren't being used

### High API costs

- The system uses `claude-3-5-sonnet-20241022` by default (high quality and cost-efficient)
- You can change the model in `contacts/message_generator.py` if needed (e.g., `claude-3-haiku-20240307` for lower costs)
- Consider implementing caching for similar contacts

## Updating Writing Guides

When you update the markdown files in `writing/`, the changes are automatically loaded. The system caches the context for performance, but you can clear the cache by restarting the server.

To force a reload without restarting, you could add an endpoint to clear the cache (future enhancement).

## Cost Considerations

- `claude-3-5-sonnet-20241022` is high quality and reasonably priced (~$3 per 1M input tokens, ~$15 per 1M output tokens)
- Each draft generation uses approximately 2000-3000 tokens
- Estimated cost: ~$0.01-0.02 per draft

For lower costs, you can switch to `claude-3-haiku-20240307` in `message_generator.py` (~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens).
