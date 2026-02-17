"""
Message generation service that uses markdown files from writing/ folder as context.
Generates highly customized and human messages using AI.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import re
from anthropic import Anthropic
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class MessageGenerator:
    """Generates personalized messages using writing guide markdown files as context."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the message generator.
        
        Args:
            api_key: Anthropic API key (or from env ANTHROPIC_API_KEY)
        """
        # Ensure .env is loaded (in case it wasn't loaded earlier)
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)  # Use override=True to ensure latest values are loaded
            logger.debug(f"Loaded .env from {env_path}")
        else:
            logger.warning(f".env file not found at {env_path}")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        logger.debug(f"API key found: {bool(self.api_key)}, key length: {len(self.api_key) if self.api_key else 0}")
        if not self.api_key:
            logger.error(f"ANTHROPIC_API_KEY not found. .env path: {env_path}, exists: {env_path.exists()}")
            if env_path.exists():
                raise ValueError(
                    "Anthropic API key is required. Add ANTHROPIC_API_KEY to your .env file. "
                    "See contacts/MESSAGE_GENERATION_SETUP.md for setup instructions."
                )
            else:
                raise ValueError(
                    f"Anthropic API key is required. .env file not found at {env_path}. "
                    "Create a .env file and add ANTHROPIC_API_KEY. See contacts/MESSAGE_GENERATION_SETUP.md for setup instructions."
                )
        
        self.client = Anthropic(api_key=self.api_key)
        self.writing_dir = Path(__file__).parent.parent / "writing"
        self._context_cache = None
    
    def _load_writing_context(self) -> str:
        """Load all markdown files from writing/ folder and combine into context."""
        if self._context_cache is not None:
            return self._context_cache
        
        context_parts = []
        files_to_load = [
            "00_CURRENT_CONTEXT.md",
            "01_SYSTEM_PROMPT.md",
            "02_VOICE_GUIDE.md",
            "03_CATEGORY_GUIDE.md",
            "04_CONTEXT_SCHEMA.md",
            "05_ANTI_PATTERNS.md",
            "06_GOLD_EXAMPLES.md",
        ]
        
        for filename in files_to_load:
            file_path = self.writing_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        context_parts.append(f"# {filename}\n\n{content}\n\n")
                        logger.debug(f"Loaded {filename}")
                except Exception as e:
                    logger.warning(f"Failed to load {filename}: {e}")
            else:
                logger.warning(f"Writing guide file not found: {file_path}")
        
        if not context_parts:
            logger.error("No writing guide files were loaded. Check that the writing/ folder exists and contains the required markdown files.")
            raise ValueError(
                "No writing guide files found. Ensure the writing/ folder exists and contains the required markdown files."
            )
        
        logger.info(f"Loaded {len(context_parts)} writing guide files")
        self._context_cache = "\n---\n\n".join(context_parts)
        return self._context_cache
    
    def _determine_category(self, contact: Dict[str, Any]) -> str:
        """
        Determine the message category based on contact data.
        
        Returns one of:
        - "warm_reengagement" (existing contact)
        - "cold_intro_shared_network" (new contact with shared group)
        - "cold_intro_no_network" (new contact without shared network)
        - "post_call_followup" (after a call/meeting)
        - "warm_intro_request" (asking for an intro)
        - "client_prospect_nurture" (Mavnox client/prospect)
        """
        contact_type = (contact.get("type") or "").lower()
        status = (contact.get("status") or "").lower()
        group = (contact.get("group") or "").strip()
        has_last_contact = contact.get("last_contact_date") is not None
        
        # Check if this is a post-call followup (would need notes or recent interaction)
        notes = contact.get("notes") or ""
        notes_lower = notes.lower() if isinstance(notes, str) else ""
        if notes_lower and ("call" in notes_lower or "conversation" in notes_lower):
            return "post_call_followup"
        
        # Existing contact = warm reengagement
        if contact_type == "existing" or status == "existing" or has_last_contact:
            return "warm_reengagement"
        
        # New contact with shared network
        if group and group.lower() not in ["other", ""]:
            return "cold_intro_shared_network"
        
        # New contact without shared network
        return "cold_intro_no_network"
    
    def _determine_channel(self, contact: Dict[str, Any]) -> str:
        """
        Determine message channel based on contact data.
        
        Channel selection rules:
        1. Phone number exists -> TEXT (default)
        2. No phone but email exists -> EMAIL
        3. Both exist -> TEXT first
        4. Neither -> EMAIL (fallback)
        """
        has_email = bool((contact.get("email") or "").strip())
        has_phone = bool((contact.get("phone") or "").strip())
        
        if has_phone:
            return "text"
        elif has_email:
            return "email"
        else:
            return "email"  # Fallback

    def _ensure_name_fields(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure contact has first_name/last_name fields derived from 'name' when missing.
        Returns a shallow-copied dict so callers can safely mutate.
        """
        updated = dict(contact or {})
        if updated.get("first_name"):
            return updated

        full_name = (updated.get("name") or "").strip()
        if not full_name or full_name.lower() == "unnamed contact":
            return updated

        # Handle "Last, First ..." format
        if "," in full_name:
            last, rest = full_name.split(",", 1)
            rest_parts = rest.strip().split()
            if rest_parts:
                updated["first_name"] = rest_parts[0]
                updated["last_name"] = last.strip() or updated.get("last_name")
                return updated

        parts = full_name.split()
        if parts:
            updated["first_name"] = parts[0]
            if len(parts) > 1:
                updated["last_name"] = " ".join(parts[1:])
        return updated

    def _replace_name_placeholders(self, text: str, first_name: Optional[str]) -> str:
        """Replace common name placeholders like [name] / {name} with the contact's first name."""
        if not text:
            return text
        replacement = (first_name or "").strip()
        if not replacement:
            return text

        patterns = [
            r"\[(?:name|first\s*name|first_name|firstname)\]",
            r"\{(?:name|first\s*name|first_name|firstname)\}",
            r"\{\{(?:name|first\s*name|first_name|firstname)\}\}",
        ]
        out = text
        for p in patterns:
            out = re.sub(p, replacement, out, flags=re.IGNORECASE)
        return out
    
    def generate_draft(
        self,
        contact: Dict[str, Any],
        batch_id: Optional[str] = None,
        recent_drafts: Optional[list] = None,
        channel_override: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a personalized message draft for a contact.
        
        Args:
            contact: Contact data dictionary
            batch_id: Optional batch ID for variation tracking
            recent_drafts: List of recent drafts in this batch to avoid repetition
        
        Returns:
            Dictionary with 'subject' (for emails) and 'body' keys
        """
        # Load writing context
        writing_context = self._load_writing_context()

        # Ensure we always have first_name/last_name when possible (helps avoid [name] placeholders)
        contact = self._ensure_name_fields(contact)
        
        # Determine category and channel
        category = self._determine_category(contact)
        channel = (channel_override or "").strip().lower() if channel_override else self._determine_channel(contact)
        if channel == "sms":
            channel = "text"
        if channel not in {"email", "text"}:
            channel = self._determine_channel(contact)
        
        # Build the system prompt
        system_prompt = f"""You are Taylor Walshe's outreach drafting system. Your job is to generate emails and texts that are indistinguishable from something Taylor would write by hand.

{writing_context}

CRITICAL INSTRUCTIONS:
1. Read ALL the markdown files above carefully - they contain the complete system for generating messages
2. Before drafting, review 00_CURRENT_CONTEXT.md for Taylor's current status
3. Review 02_VOICE_GUIDE.md to match Taylor's writing style exactly
4. Review 03_CATEGORY_GUIDE.md to select the right approach for this contact type
5. Review 04_CONTEXT_SCHEMA.md to understand what contact data fields mean and how to use them
6. Review 05_ANTI_PATTERNS.md and check your draft against every item
7. Review 06_GOLD_EXAMPLES.md to calibrate quality

After drafting, verify:
- No patterns from 05_ANTI_PATTERNS.md appear
- The message feels unique and human-written
- All variables are properly populated (no broken references)
- The Once-Only Rule is followed (no repeated key nouns/phrases)
- Channel tone is correct (text vs email)
- If this is part of a batch, ensure variation from other drafts"""
        
        # Build user prompt with contact data
        contact_summary = self._format_contact_data(contact)
        first_name = (contact.get("first_name") or "").strip()
        
        variation_note = ""
        if recent_drafts:
            variation_note = f"\n\nIMPORTANT: You have already generated {len(recent_drafts)} draft(s) in this batch. Ensure this draft is structurally and linguistically different from those. Vary the opening move, CTA phrasing, and sentence structure."
        
        user_prompt = f"""Generate a {channel} message for the following contact:

{contact_summary}

Category: {category}
Channel: {channel}
First name to use (never use placeholders like [name]): {first_name or "there"}
{variation_note}

Output format:
- For emails: Start with "SUBJECT: [subject line]" followed by a blank line, then the body
- For texts: Just output the message body (no subject line, no greeting/sign-off unless they don't know Taylor)

Generate the message now, following all the guidelines in the markdown files above."""
        
        try:
            # Claude uses a different API structure - system message is separate
            # Try models in order of preference (fallback if one doesn't work)
            models_to_try = [
                "claude-3-5-sonnet-20240620",  # Claude 3.5 Sonnet (June 2024)
                "claude-3-sonnet-20240229",     # Claude 3 Sonnet (fallback)
                "claude-3-haiku-20240307",      # Claude 3 Haiku (fastest, always available)
            ]
            
            last_error = None
            for model in models_to_try:
                try:
                    response = self.client.messages.create(
                        model=model,
                        max_tokens=1024,
                        temperature=0.8,  # Higher temperature for more variation
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                    logger.info(f"Successfully used model: {model}")
                    break
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    if '404' in error_str or 'not_found' in error_str.lower():
                        logger.warning(f"Model {model} not available, trying next...")
                        continue
                    else:
                        # Non-404 error (auth, rate limit, etc.) - re-raise
                        raise
            
            if 'response' not in locals():
                raise Exception(f"All models failed. Last error: {last_error}")
            
            draft_text = response.content[0].text.strip()
            
            # Parse the response
            if channel == "email":
                if draft_text.startswith("SUBJECT:"):
                    parts = draft_text.split("\n\n", 1)
                    if len(parts) == 2:
                        subject = parts[0].replace("SUBJECT:", "").strip()
                        body = parts[1].strip()
                    else:
                        # Fallback: try to extract subject from first line
                        lines = draft_text.split("\n")
                        if lines[0].startswith("SUBJECT:"):
                            subject = lines[0].replace("SUBJECT:", "").strip()
                            body = "\n".join(lines[1:]).strip()
                        else:
                            subject = "Quick question"
                            body = draft_text
                else:
                    # No subject line found, use default
                    subject = "Quick question"
                    body = draft_text

                # Safety-net: replace [name] placeholders if Claude outputs them
                subject = self._replace_name_placeholders(subject, first_name)
                body = self._replace_name_placeholders(body, first_name)
                
                return {
                    "subject": subject,
                    "body": body,
                    "channel": "email"
                }
            else:
                # Text message - just return the body
                body = self._replace_name_placeholders(draft_text, first_name)
                return {
                    "subject": "",
                    "body": body,
                    "channel": "text"
                }
                
        except Exception as e:
            logger.error(f"Error generating message draft: {e}", exc_info=True)
            raise Exception(f"Failed to generate message draft: {str(e)}")
    
    def _format_contact_data(self, contact: Dict[str, Any]) -> str:
        """Format contact data into a readable summary for the AI."""
        lines = []
        
        # Identity
        if contact.get("first_name"):
            lines.append(f"First Name: {contact['first_name']}")
        if contact.get("last_name"):
            lines.append(f"Last Name: {contact['last_name']}")
        
        # Relationship
        lines.append(f"Type: {contact.get('type', 'unknown')}")
        lines.append(f"Status: {contact.get('status', 'unknown')}")
        lines.append(f"Group: {contact.get('group', 'N/A')}")
        if contact.get('group_name'):
            lines.append(f"Group Name: {contact['group_name']}")
        lines.append(f"Relationship Warmth: {contact.get('relationship_warmth', 'unknown')}")
        if contact.get('last_contact_date'):
            lines.append(f"Last Contact Date: {contact['last_contact_date']}")
        
        # Professional
        if contact.get('company'):
            lines.append(f"Company: {contact['company']}")
        if contact.get('current_role'):
            lines.append(f"Current Role: {contact['current_role']}")
        if contact.get('previous_company'):
            lines.append(f"Previous Company: {contact['previous_company']}")
        if contact.get('previous_role'):
            lines.append(f"Previous Role: {contact['previous_role']}")
        if contact.get('industry'):
            lines.append(f"Industry: {contact['industry']}")
        if contact.get('career_path_type'):
            lines.append(f"Career Path Type: {contact['career_path_type']}")
        
        # Context
        if contact.get('location'):
            lines.append(f"Location: {contact['location']}")
        if contact.get('notes'):
            lines.append(f"Notes: {contact['notes']}")
        if contact.get('prior_interactions'):
            lines.append(f"Prior Interactions: {contact['prior_interactions']}")
        if contact.get('recent_activity'):
            lines.append(f"Recent Activity: {contact['recent_activity']}")
        if contact.get('mutual_connections'):
            lines.append(f"Mutual Connections: {contact['mutual_connections']}")
        
        # Outreach metadata
        if contact.get('outreach_goal'):
            lines.append(f"Outreach Goal: {contact['outreach_goal']}")
        if contact.get('topic'):
            lines.append(f"Topic: {contact['topic']}")
        if contact.get('batch_id'):
            lines.append(f"Batch ID: {contact['batch_id']}")
        
        return "\n".join(lines)
    
    def clear_cache(self):
        """Clear the context cache (useful if markdown files are updated)."""
        self._context_cache = None
        logger.info("Writing context cache cleared")
