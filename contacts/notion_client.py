"""
Notion API Client for Contact Management

Handles all interactions with Notion database for contacts.
"""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from notion_client import Client
from notion_client.errors import APIResponseError
import logging
import time

logger = logging.getLogger(__name__)


class NotionContactClient:
    """Client for managing contacts in Notion database."""
    
    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize Notion client.
        
        Args:
            api_key: Notion integration token (or from env NOTION_API_KEY)
            database_id: Notion database ID (or from env NOTION_DATABASE_ID)
        """
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        
        if not self.api_key:
            raise ValueError("Notion API key is required. Set NOTION_API_KEY environment variable.")
        if not self.database_id:
            raise ValueError("Notion database ID is required. Set NOTION_DATABASE_ID environment variable.")
        
        # Initialize client with timeout settings
        self.client = Client(
            auth=self.api_key,
            timeout_ms=30000  # 30 second timeout for API calls
        )
    
    def _get_linkedin_url(self, properties: Dict) -> Optional[str]:
        """
        Extract LinkedIn URL from Notion properties.
        Tries multiple methods: URL property, rich_text with link, or plain rich_text.
        Handles various Notion property types that might store URLs.
        """
        # Find the property key first
        actual_key = self._find_property_key(properties, ["Linkedin", "LinkedIn URL", "linkedin_url", "LinkedIn url", "LinkedIn"])
        if actual_key is None:
            logger.debug("LinkedIn URL property not found in Notion properties")
            return None
        
        prop = properties[actual_key]
        prop_type = prop.get("type")
        
        logger.debug(f"Found LinkedIn URL property '{actual_key}' with type '{prop_type}'")
        
        # Handle URL property type (most common for external links)
        if prop_type == "url":
            url_value = prop.get("url")
            if url_value:
                logger.debug(f"Extracted LinkedIn URL from url property: {url_value}")
                return url_value
            else:
                logger.debug(f"URL property exists but is empty/null")
        
        # Handle rich_text property (text properties show up as rich_text in API)
        if prop_type == "rich_text":
            rich_text_array = prop.get("rich_text", [])
            if rich_text_array and len(rich_text_array) > 0:
                # Try to extract from all elements in the array (text can be split across multiple elements)
                full_text = ""
                for element in rich_text_array:
                    # Notion rich_text links are in text.link.url structure
                    if "text" in element:
                        text_obj = element["text"]
                        if "link" in text_obj and text_obj["link"]:
                            link_url = text_obj["link"].get("url")
                            if link_url:
                                logger.debug(f"Extracted LinkedIn URL from rich_text link: {link_url}")
                                return link_url
                        # Also check for href directly (some variations)
                        if "href" in text_obj:
                            href_url = text_obj["href"]
                            if href_url:
                                logger.debug(f"Extracted LinkedIn URL from rich_text href: {href_url}")
                                return href_url
                    
                    # Collect plain_text from all elements
                    plain_text = element.get("plain_text", "")
                    if plain_text:
                        full_text += plain_text
                
                # Now check the full combined text
                if full_text:
                    full_text = full_text.strip()
                    # Check if it looks like a URL
                    if full_text.startswith("http://") or full_text.startswith("https://"):
                        logger.debug(f"Extracted LinkedIn URL from rich_text plain_text: {full_text}")
                        return full_text
                    # Check if it contains linkedin.com
                    if "linkedin.com" in full_text.lower():
                        # If it doesn't start with http, add https://
                        if not full_text.startswith("http"):
                            full_text = "https://" + full_text
                        logger.debug(f"Extracted and normalized LinkedIn URL from rich_text: {full_text}")
                        return full_text
                    # If it's just plain text that might be a URL, return it anyway
                    # (user might have pasted just the domain)
                    if full_text and len(full_text) > 5:  # Basic sanity check
                        logger.debug(f"Returning plain text as potential URL: {full_text}")
                        return full_text
            else:
                logger.debug(f"rich_text property exists but is empty")
        
        # Try using _get_property_value with rich_text type (for text properties)
        try:
            text_value = self._get_property_value(properties, [actual_key], "rich_text")
            if text_value:
                text_value = text_value.strip()
                # Check if it looks like a URL
                if text_value.startswith("http://") or text_value.startswith("https://"):
                    logger.debug(f"Extracted LinkedIn URL via _get_property_value (rich_text): {text_value}")
                    return text_value
                # Check if it contains linkedin.com
                if "linkedin.com" in text_value.lower():
                    if not text_value.startswith("http"):
                        text_value = "https://" + text_value
                    logger.debug(f"Extracted and normalized LinkedIn URL via _get_property_value: {text_value}")
                    return text_value
                # Return the text value anyway if it exists
                if text_value:
                    logger.debug(f"Returning text value as potential URL: {text_value}")
                    return text_value
        except Exception as e:
            logger.debug(f"Error in _get_property_value (rich_text) fallback: {e}")
        
        # Handle formula property (if it's a formula that returns a URL)
        if prop_type == "formula":
            formula_obj = prop.get("formula", {})
            if formula_obj:
                # Formula can return different types
                if "string" in formula_obj:
                    url_value = formula_obj["string"]
                    if url_value and ("linkedin.com" in url_value.lower() or url_value.startswith("http")):
                        logger.debug(f"Extracted LinkedIn URL from formula: {url_value}")
                        return url_value
        
        # Try using _get_property_value as fallback (handles url type)
        try:
            url_value = self._get_property_value(properties, [actual_key], "url")
            if url_value:
                logger.debug(f"Extracted LinkedIn URL via _get_property_value fallback: {url_value}")
                return url_value
        except Exception as e:
            logger.debug(f"Error in _get_property_value fallback: {e}")
        
        # Log the full property structure for debugging
        logger.debug(f"Could not extract LinkedIn URL. Property structure: {prop}")
        
        return None
    
    def _clean_group_value(self, group_value: Optional[str]) -> Optional[str]:
        """
        Clean and normalize group value by removing trailing parentheses and mapping to standard values.
        This handles cases where Notion has values like "McKinsey)" instead of "McK".
        Used when reading from Notion.
        """
        if not group_value:
            return None
        # Strip trailing parentheses and whitespace
        cleaned = group_value.strip().rstrip(')').strip()
        if not cleaned:
            return None
        
        # Normalize to standard group values (case-insensitive)
        cleaned_lower = cleaned.lower()
        group_map = {
            'fam': 'fam',
            'family': 'fam',
            'mck': 'McK',
            'mckinsey': 'McK',
            'mckinsey)': 'McK',  # Handle with parenthesis
            'pea': 'PEA',
            'phillips exeter academy': 'PEA',
            'exeter': 'PEA',
            'gu': 'GU',
            'georgetown': 'GU',
            'georgetown university': 'GU',
            'bp': 'BP',
            'berkshire partners': 'BP',
            'berkshire': 'BP',
            'mba': 'MBA',
            'mvnx': 'MVNX',
            'mavnox': 'MVNX',
            'other': 'other'
        }
        
        # Try exact match first
        if cleaned_lower in group_map:
            return group_map[cleaned_lower]
        
        # Try partial match
        for key, value in group_map.items():
            if key in cleaned_lower or cleaned_lower in key:
                return value
        
        # If no match, return cleaned original (might be a new group value)
        return cleaned
    
    def _normalize_group_for_notion(self, group_value: Optional[str]) -> Optional[str]:
        """
        Normalize group value for writing to Notion.
        Converts internal format to Notion format (standardizes case and format).
        Used when writing to Notion.
        """
        if not group_value:
            return None
        
        # Clean the value first
        cleaned = group_value.strip()
        if not cleaned:
            return None
        
        # Map internal values to Notion format
        # Notion typically uses the standard abbreviations (McK, PEA, GU, etc.)
        # but we normalize case and handle variations
        cleaned_lower = cleaned.lower()
        notion_group_map = {
            'fam': 'Fam',
            'family': 'Fam',
            'mck': 'McK',
            'mckinsey': 'McK',
            'pea': 'PEA',
            'phillips exeter academy': 'PEA',
            'exeter': 'PEA',
            'gu': 'GU',
            'georgetown': 'GU',
            'georgetown university': 'GU',
            'bp': 'BP',
            'berkshire partners': 'BP',
            'berkshire': 'BP',
            'mba': 'MBA',
            'mvnx': 'MVNX',
            'mavnox': 'MVNX',
            'other': 'Other'
        }
        
        # Try exact match first
        if cleaned_lower in notion_group_map:
            return notion_group_map[cleaned_lower]
        
        # Try partial match
        for key, value in notion_group_map.items():
            if key in cleaned_lower or cleaned_lower in key:
                return value
        
        # If no match, return the cleaned value with proper capitalization
        # (capitalize first letter, keep rest as-is)
        return cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
    
    def _find_property_key(self, properties: Dict, possible_keys: List[str]) -> Optional[str]:
        """
        Find a property key in Notion properties, trying multiple variations.
        Handles case-insensitive matching and different naming conventions.
        """
        # First try exact matches
        for key in possible_keys:
            if key in properties:
                return key
        
        # Then try case-insensitive matches
        properties_lower = {k.lower(): k for k in properties.keys()}
        for key in possible_keys:
            if key.lower() in properties_lower:
                return properties_lower[key.lower()]
        
        return None
    
    def _map_notion_to_contact(self, notion_page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map Notion page properties to our contact data model.
        
        This function handles the mapping between Notion's property structure
        and our standardized contact model. Supports capitalized property names.
        """
        properties = notion_page.get("properties", {})
        
        # Property name mappings - match your actual Notion property names
        # Normalize status/type values to lowercase to match validation requirements
        raw_status = self._get_property_value(properties, ["Status", "status"], "status")
        raw_type = self._get_property_value(properties, ["Type", "type"], "status")
        
        # Normalize status: "Done" -> "done", "Scheduled" -> "scheduled", etc.
        status_map = {
            "Done": "done",
            "Scheduled": "scheduled", 
            "Circle Back": "circle_back",
            "Circle back": "circle_back",
            "Need to contact": "need_to_contact",
            "need to contact": "need_to_contact",  # Handle lowercase version with spaces
            "Contacted": "contacted",
            "Queued": "queued",
            "Wait": "wait",
            "Ghosted": "ghosted"
        }
        # If not in map, try to normalize: lowercase and replace spaces with underscores
        if raw_status and raw_status not in status_map:
            normalized_status = raw_status.lower().replace(" ", "_")
        else:
            normalized_status = status_map.get(raw_status, None)
        
        # Normalize type: "Existing" -> "existing", "2026 New" -> "2026_new"
        type_map = {
            "Existing": "existing",
            "2026 New": "2026_new",
            "2026_new": "2026_new"  # Already correct
        }
        normalized_type = type_map.get(raw_type, raw_type.lower() if raw_type else None)
        
        # Get name and handle empty names
        raw_name = self._get_property_value(properties, ["Contact", "Name", "name"], "title")
        contact_name = raw_name.strip() if raw_name else "Unnamed Contact"

        # Derive first/last name for downstream personalization (AI drafts, greetings, etc.)
        first_name = None
        last_name = None
        if contact_name and contact_name.lower() != "unnamed contact":
            name_str = contact_name.strip()
            if "," in name_str:
                # Handle "Last, First ..." format
                last, rest = name_str.split(",", 1)
                rest_parts = rest.strip().split()
                if rest_parts:
                    first_name = rest_parts[0]
                    last_name = last.strip() or None
            else:
                parts = name_str.split()
                if parts:
                    first_name = parts[0]
                    if len(parts) > 1:
                        last_name = " ".join(parts[1:])
        
        # Get last_edited_time from Notion page metadata
        last_edited_time = None
        if "last_edited_time" in notion_page:
            last_edited_time = notion_page["last_edited_time"]
        
        contact = {
            "id": notion_page.get("id"),
            "name": contact_name,
            "first_name": first_name,
            "last_name": last_name,
            "email": self._get_property_value(properties, ["Email", "email"], "rich_text"),  # Your Email is rich_text, not email type
            "phone": self._get_property_value(properties, ["Phone", "phone"], "phone_number"),
            "status": normalized_status,  # Normalized to lowercase
            "type": normalized_type,  # Normalized to lowercase
            "group": self._clean_group_value(self._get_property_value(properties, ["Group", "group"], "status")),  # Your Group is status type, clean trailing parentheses
            "relationship_type": self._get_property_value(properties, ["Relationship Type", "relationship_type", "Relationship type"], "status"),
            "title": self._get_property_value(properties, ["Role", "role", "Title", "title"], "rich_text"),  # Prioritize Role over Title
            "company": self._get_property_value(properties, ["Company", "company"], "rich_text"),
            "industry": self._get_property_value(properties, ["Industry", "industry"], "rich_text"),
            "location": self._get_property_value(properties, ["Location", "location"], "rich_text"),
            "linkedin_url": self._get_linkedin_url(properties),
            "last_contact_date": self._get_property_value(properties, ["Last contact date", "Last Contact Date", "last_contact_date"], "date"),
            "days_at_current_status": self._get_property_value(properties, ["Days", "Days at current status", "Days At Current Status", "days_at_current_status"], "formula"),  # Your Days is a formula
            "call_count": self._get_property_value(properties, ["Count", "Call Count", "call_count"], "number") or 0,
            "notes": self._get_property_value(properties, ["Notes", "notes"], "rich_text"),
            "created_date": self._get_property_value(properties, ["Created date", "Created Date", "created_date"], "date"),
            "next_followup_date": self._get_property_value(properties, ["Next followup date", "Next Followup Date", "next_followup_date"], "date"),
            "followup_context": self._get_property_value(properties, ["Followup context", "Followup Context", "followup_context"], "rich_text"),
            "_notion_last_edited_time": last_edited_time,  # Internal field for conflict resolution
        }
        
        return contact
    
    def _get_property_value(self, properties: Dict, keys: Any, prop_type: str) -> Any:
        """
        Extract value from Notion property based on type.
        
        Args:
            properties: Notion properties dictionary
            keys: Single key string or list of possible keys to try
            prop_type: Type of property (title, email, select, etc.)
        """
        # Handle both single key and list of keys
        if isinstance(keys, str):
            keys = [keys]
        
        # Find the actual key in properties
        actual_key = self._find_property_key(properties, keys)
        if actual_key is None:
            return None
        
        prop = properties[actual_key]
        
        try:
            if prop_type == "title":
                title_array = prop.get("title", [])
                return title_array[0].get("plain_text", "") if title_array else ""
            elif prop_type == "rich_text":
                rich_text_array = prop.get("rich_text", [])
                return rich_text_array[0].get("plain_text", "") if rich_text_array else ""
            elif prop_type == "rich_text_url":
                # Extract URL from rich_text that contains a link
                rich_text_array = prop.get("rich_text", [])
                if rich_text_array:
                    # Check if the first element has a link
                    first_element = rich_text_array[0]
                    # Notion rich_text links are in text.link.href structure
                    if "text" in first_element and "link" in first_element["text"]:
                        return first_element["text"]["link"].get("url")
                    # Also check direct href (some variations)
                    if "href" in first_element:
                        return first_element["href"]
                return None
            elif prop_type == "email":
                return prop.get("email")
            elif prop_type == "phone_number":
                return prop.get("phone_number")
            elif prop_type == "url":
                url_value = prop.get("url")
                # If URL property is empty, try to get from rich_text as fallback
                if not url_value:
                    rich_text_array = prop.get("rich_text", [])
                    if rich_text_array:
                        first_element = rich_text_array[0]
                        # Notion rich_text links are in text.link.href structure
                        if "text" in first_element and "link" in first_element["text"]:
                            return first_element["text"]["link"].get("url")
                        # Also check direct href (some variations)
                        if "href" in first_element:
                            return first_element["href"]
                return url_value
            elif prop_type == "select":
                select_obj = prop.get("select")
                return select_obj.get("name") if select_obj else None
            elif prop_type == "status":
                # Notion status type (similar to select but different structure)
                status_obj = prop.get("status")
                return status_obj.get("name") if status_obj else None
            elif prop_type == "formula":
                # Notion formula type - extract the result
                formula_obj = prop.get("formula")
                if formula_obj:
                    # Formula can return different types (number, string, date, etc.)
                    if "number" in formula_obj:
                        return formula_obj["number"]
                    elif "string" in formula_obj:
                        return formula_obj["string"]
                    elif "date" in formula_obj:
                        date_obj = formula_obj["date"]
                        return date_obj.get("start") if date_obj else None
                return None
            elif prop_type == "date":
                date_obj = prop.get("date")
                if date_obj and date_obj.get("start"):
                    return date_obj["start"]
                return None
            elif prop_type == "number":
                return prop.get("number")
            elif prop_type == "checkbox":
                return prop.get("checkbox", False)
            else:
                return None
        except (KeyError, IndexError, AttributeError) as e:
            logger.warning(f"Error extracting {actual_key} ({prop_type}): {e}")
            return None
    
    def _get_notion_property_name(self, properties: Dict, possible_names: List[str]) -> str:
        """
        Get the actual property name from Notion properties.
        Tries to find existing property first, otherwise uses the first possible name.
        """
        # Try to find existing property
        found = self._find_property_key(properties, possible_names)
        if found:
            return found
        # If not found, use the first capitalized version (most common)
        return possible_names[0]
    
    def _map_contact_to_notion(self, contact: Dict[str, Any], existing_properties: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Map our contact data model to Notion page properties.
        
        This creates the property structure that Notion expects.
        Supports capitalized property names by checking existing properties.
        """
        if existing_properties is None:
            existing_properties = {}
        
        properties = {}
        
        # Required fields - try to match existing property name
        if "name" in contact:
            name_key = self._get_notion_property_name(existing_properties, ["Contact", "Name", "name"])
            properties[name_key] = {
                "title": [{"text": {"content": str(contact["name"])}}]
            }
        
        # Helper function to convert status from internal format to Notion format
        def normalize_status_to_notion(status_value):
            """Convert internal status format (lowercase with underscores) to Notion format (capitalized with spaces)."""
            if not status_value:
                return None
            status_map = {
                "wait": "Wait",
                "queued": "Queued",
                "queue": "Queue",  # Handle both "queue" and "queued" variations
                "need_to_contact": "Need to Contact",
                "contacted": "Contacted",
                "circle_back": "Circle Back",
                "scheduled": "Scheduled",
                "done": "Done",
                "ghosted": "Ghosted"
            }
            return status_map.get(status_value, status_value.replace("_", " ").title())
        
        # Helper function to convert type from internal format to Notion format
        def normalize_type_to_notion(type_value):
            """Convert internal type format to Notion format."""
            if not type_value:
                return None
            if type_value == "2026_new":
                return "2026 New"
            elif type_value == "existing":
                return "Existing"
            return type_value
        
        # Helper function for group normalization (needed for lambda)
        def normalize_group_for_notion(group_value):
            return self._normalize_group_for_notion(group_value)
        
        # Optional fields - only include if they have values
        # Format: (field_name, [possible_notion_names], mapper_function)
        field_mappings = [
            ("email", ["Email", "email"], lambda v: {"rich_text": [{"text": {"content": str(v)}}]}),  # Your Email is rich_text
            ("phone", ["Phone", "phone"], lambda v: {"phone_number": v}),
            ("status", ["Status", "status"], lambda v: {"status": {"name": normalize_status_to_notion(v)}} if v else None),  # Your Status is status type
            ("type", ["Type", "type"], lambda v: {"status": {"name": normalize_type_to_notion(v)}} if v else None),  # Your Type is status type
            ("group", ["Group", "group"], lambda v: {"status": {"name": normalize_group_for_notion(v)}} if v else None),  # Your Group is status type, normalize before writing
            ("relationship_type", ["Relationship Type", "relationship_type"], lambda v: {"status": {"name": v}} if v else None),
            ("title", ["Role", "role", "Title", "title"], lambda v: {"rich_text": [{"text": {"content": str(v)}}]}),  # Prioritize Role over Title
            ("company", ["Company", "company"], lambda v: {"rich_text": [{"text": {"content": str(v)}}]}),
            ("industry", ["Industry", "industry"], lambda v: {"rich_text": [{"text": {"content": str(v)}}]}),
            ("location", ["Location", "location"], lambda v: {"rich_text": [{"text": {"content": str(v)}}]}),
            ("linkedin_url", ["Linkedin", "LinkedIn URL", "linkedin_url", "LinkedIn"], lambda v: {"rich_text": [{"text": {"content": str(v)}}]}),  # Changed to rich_text
            ("notes", ["Notes", "notes"], lambda v: {"rich_text": [{"text": {"content": str(v)}}]}),
            ("followup_context", ["Followup context", "followup_context"], lambda v: {"rich_text": [{"text": {"content": str(v)}}]}),
            ("call_count", ["Count", "Call Count", "call_count"], lambda v: {"number": int(v)} if v is not None else None),
            # Note: "Days" is a formula in your database, so we can't write to it directly
            # ("days_at_current_status", ["Days", "Days at current status"], ...) - skipped, formula is read-only
        ]
        
        date_mappings = [
            ("last_contact_date", ["Last contact date", "Last Contact Date", "last_contact_date"]),
            ("created_date", ["Created date", "Created Date", "created_date"]),
            ("next_followup_date", ["Next followup date", "Next Followup Date", "next_followup_date"]),
        ]
        
        # Map regular fields
        for field, possible_names, mapper in field_mappings:
            if field in contact and contact[field] is not None:
                # Skip empty strings - they should be treated as None
                value = contact[field]
                if isinstance(value, str) and not value.strip():
                    continue
                
                mapped_value = mapper(value)
                if mapped_value is not None:
                    # For phone_number, ensure it's not an empty string
                    if "phone_number" in mapped_value:
                        if not mapped_value["phone_number"] or not mapped_value["phone_number"].strip():
                            continue  # Skip empty phone numbers
                    
                    notion_key = self._get_notion_property_name(existing_properties, possible_names)
                    properties[notion_key] = mapped_value
        
        # Map date fields
        for field, possible_names in date_mappings:
            if field in contact and contact[field]:
                date_value = contact[field]
                # Skip empty strings
                if isinstance(date_value, str) and not date_value.strip():
                    continue
                notion_key = self._get_notion_property_name(existing_properties, possible_names)
                if isinstance(date_value, str):
                    properties[notion_key] = {"date": {"start": date_value}}
                elif isinstance(date_value, (date, datetime)):
                    properties[notion_key] = {"date": {"start": date_value.isoformat()}}
        
        return properties
    
    def get_all_contacts(self, page_size: int = 100, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch all contacts from Notion database with retry logic.
        
        Args:
            page_size: Number of results per page (max 100)
            max_retries: Maximum number of retry attempts for failed requests
        
        Returns:
            List of contact dictionaries
        """
        contacts = []
        has_more = True
        start_cursor = None
        
        retry_count = 0
        
        try:
            while has_more:
                query_params = {
                    "database_id": self.database_id,
                    "page_size": min(page_size, 100),
                }
                if start_cursor:
                    query_params["start_cursor"] = start_cursor
                
                # Retry logic for API calls
                response = None
                last_error = None
                for attempt in range(max_retries):
                    try:
                        response = self.client.databases.query(**query_params)
                        retry_count = 0  # Reset retry count on success
                        break
                    except (APIResponseError, Exception) as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 1  # Exponential backoff: 1s, 2s, 3s
                            logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                            time.sleep(wait_time)
                        else:
                            raise
                
                if response is None:
                    raise last_error
                
                for page in response.get("results", []):
                    try:
                        contact = self._map_notion_to_contact(page)
                        contacts.append(contact)
                    except Exception as e:
                        logger.warning(f"Error mapping contact: {e}, skipping...")
                        continue
                
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
                
                # Small delay between pages to avoid rate limiting
                if has_more:
                    time.sleep(0.1)
                
        except APIResponseError as e:
            logger.error(f"Notion API error fetching contacts: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching contacts: {e}")
            raise
        
        return contacts
    
    def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single contact by ID.
        
        Args:
            contact_id: Notion page ID
        
        Returns:
            Contact dictionary or None if not found
        """
        try:
            page = self.client.pages.retrieve(contact_id)
            return self._map_notion_to_contact(page)
        except APIResponseError as e:
            if e.code == "object_not_found":
                return None
            logger.error(f"Notion API error fetching contact {contact_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching contact {contact_id}: {e}")
            raise
    
    def create_contact(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new contact in Notion.
        
        Args:
            contact: Contact data dictionary
        
        Returns:
            Created contact dictionary
        """
        # Validate required fields
        if not contact.get("name"):
            raise ValueError("Name is required")
        if not contact.get("email") and not contact.get("phone"):
            raise ValueError("At least one of email or phone is required")
        
        # Set defaults
        if "status" not in contact:
            contact["status"] = "queued"
        if "created_date" not in contact:
            contact["created_date"] = datetime.now().date().isoformat()
        if "days_at_current_status" not in contact:
            contact["days_at_current_status"] = 0
        
        # Get database schema to use correct property names
        try:
            database = self.client.databases.retrieve(self.database_id)
            existing_properties = database.get("properties", {})
        except APIResponseError as e:
            logger.warning(f"Could not retrieve database schema, using default property names: {e}")
            existing_properties = {}
        
        properties = self._map_contact_to_notion(contact, existing_properties)
        
        try:
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            return self._map_notion_to_contact(page)
        except APIResponseError as e:
            error_msg = str(e)
            # Log the full error details for debugging
            logger.error(f"Notion API error creating contact: {error_msg}")
            if hasattr(e, 'body') and e.body:
                logger.error(f"Notion API error body: {e.body}")
            # Re-raise with a more user-friendly message
            raise ValueError(f"Failed to create contact in Notion: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error creating contact: {error_msg}", exc_info=True)
            raise ValueError(f"Failed to create contact: {error_msg}")
    
    def update_contact(self, contact_id: str, contact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing contact in Notion.
        
        Args:
            contact_id: Notion page ID
            contact: Contact data dictionary with fields to update
        
        Returns:
            Updated contact dictionary
        """
        # Get existing page to preserve property name casing
        try:
            existing_page = self.client.pages.retrieve(contact_id)
            existing_properties = existing_page.get("properties", {})
        except APIResponseError as e:
            if e.code == "object_not_found":
                raise ValueError(f"Contact {contact_id} not found")
            raise
        
        properties = self._map_contact_to_notion(contact, existing_properties)
        
        if not properties:
            raise ValueError("No properties to update")
        
        try:
            page = self.client.pages.update(
                page_id=contact_id,
                properties=properties
            )
            return self._map_notion_to_contact(page)
        except APIResponseError as e:
            if e.code == "object_not_found":
                raise ValueError(f"Contact {contact_id} not found")
            error_msg = str(e)
            # Log the full error details for debugging
            logger.error(f"Notion API error updating contact {contact_id}: {error_msg}")
            if hasattr(e, 'body') and e.body:
                logger.error(f"Notion API error body: {e.body}")
            # Re-raise with a more user-friendly message
            raise ValueError(f"Failed to update contact in Notion: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error updating contact {contact_id}: {error_msg}", exc_info=True)
            raise ValueError(f"Failed to update contact: {error_msg}")
    
    def delete_contact(self, contact_id: str) -> bool:
        """
        Archive/delete a contact in Notion.
        
        Note: Notion doesn't support hard delete, so we archive instead.
        
        Args:
            contact_id: Notion page ID
        
        Returns:
            True if successful
        """
        try:
            # Archive the page (Notion's way of "deleting")
            self.client.pages.update(
                page_id=contact_id,
                archived=True
            )
            return True
        except APIResponseError as e:
            logger.error(f"Notion API error deleting contact {contact_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting contact {contact_id}: {e}")
            raise
