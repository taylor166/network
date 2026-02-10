"""
FastAPI endpoints for contact management.
"""
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Optional
import logging
from datetime import datetime, date, timedelta
import time

from contacts.notion_client import NotionContactClient
from contacts.models import (
    ContactCreate, ContactUpdate, ContactResponse, ContactFilter
)
from contacts.message_models import (
    MessageSendEmail, MessageSendSMS, MessageResponse, MessageFilter,
    MessageDirection, MessageChannel, MessageCreate
)
from contacts.message_storage import MessageStorage

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Contact Management API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Notion client
notion_client = None

# Initialize message storage
message_storage = None

# Initialize email/SMS clients (lazy initialization)
gmail_manager = None
twilio_client = None

# Simple in-memory cache for contacts
_contacts_cache = None
_cache_timestamp = None
_cache_ttl = 60  # Cache for 60 seconds

# Track contacts modified in the system (to prevent Notion from overriding)
# Format: {contact_id: modification_timestamp}
_system_modified_contacts = {}

def get_notion_client() -> NotionContactClient:
    """Get or create Notion client instance."""
    global notion_client
    if notion_client is None:
        notion_client = NotionContactClient()
    return notion_client

def get_message_storage() -> MessageStorage:
    """Get or create message storage instance."""
    global message_storage
    if message_storage is None:
        message_storage = MessageStorage()
    return message_storage

def get_gmail_manager():
    """Get or create multi-account Gmail manager instance."""
    global gmail_manager
    if gmail_manager is None:
        try:
            from integrations.email.gmail_client import MultiAccountGmailManager
            gmail_manager = MultiAccountGmailManager()
        except Exception as e:
            logger.warning(f"Gmail manager not available: {e}")
            return None
    return gmail_manager

def get_twilio_client():
    """Get or create Twilio client instance."""
    global twilio_client
    if twilio_client is None:
        try:
            from integrations.sms.twilio_client import TwilioSMSClient
            twilio_client = TwilioSMSClient()
        except Exception as e:
            logger.warning(f"Twilio client not available: {e}")
            return None
    return twilio_client

def get_cached_contacts() -> Optional[List[dict]]:
    """Get contacts from cache if still valid."""
    global _contacts_cache, _cache_timestamp
    if _contacts_cache is not None and _cache_timestamp is not None:
        if time.time() - _cache_timestamp < _cache_ttl:
            logger.info(f"Returning {len(_contacts_cache)} contacts from cache")
            return _contacts_cache
    return None

def set_cached_contacts(contacts: List[dict]):
    """Store contacts in cache."""
    global _contacts_cache, _cache_timestamp
    _contacts_cache = contacts
    _cache_timestamp = time.time()
    logger.info(f"Cached {len(contacts)} contacts")

def invalidate_cache():
    """Invalidate the contacts cache."""
    global _contacts_cache, _cache_timestamp
    _contacts_cache = None
    _cache_timestamp = None

def mark_contact_as_system_modified(contact_id: str):
    """Mark a contact as modified in the system (for conflict resolution)."""
    global _system_modified_contacts
    _system_modified_contacts[contact_id] = time.time()
    logger.debug(f"Marked contact {contact_id} as system-modified at {_system_modified_contacts[contact_id]}")

def merge_contacts_with_conflict_resolution(notion_contacts: List[dict], cached_contacts: Optional[List[dict]]) -> List[dict]:
    """
    Merge contacts from Notion with cached contacts, resolving conflicts.
    System modifications take precedence over Notion changes.
    """
    global _system_modified_contacts
    
    if cached_contacts is None:
        return notion_contacts
    
    # Create a map of cached contacts by ID
    cached_map = {c["id"]: c for c in cached_contacts}
    
    merged = []
    skipped_count = 0
    
    for notion_contact in notion_contacts:
        contact_id = notion_contact.get("id")
        if not contact_id:
            merged.append(notion_contact)
            continue
        
        # Check if this contact was modified in the system
        system_modified_time = _system_modified_contacts.get(contact_id)
        
        if system_modified_time and contact_id in cached_map:
            # Contact was modified in the system - check if Notion change is newer
            notion_edited_time = notion_contact.get("_notion_last_edited_time")
            
            if notion_edited_time:
                try:
                    # Parse Notion timestamp (ISO format)
                    notion_timestamp = datetime.fromisoformat(notion_edited_time.replace("Z", "+00:00")).timestamp()
                    
                    # If system modification is more recent, keep cached version
                    if system_modified_time > notion_timestamp:
                        logger.debug(f"Skipping Notion update for {contact_id}: system modification ({system_modified_time}) is newer than Notion ({notion_timestamp})")
                        merged.append(cached_map[contact_id])
                        skipped_count += 1
                        continue
                except Exception as e:
                    logger.warning(f"Error comparing timestamps for {contact_id}: {e}")
                    # On error, prefer system modification
                    merged.append(cached_map[contact_id])
                    skipped_count += 1
                    continue
            else:
                # No Notion timestamp - prefer system modification
                logger.debug(f"Skipping Notion update for {contact_id}: no Notion timestamp, keeping system modification")
                merged.append(cached_map[contact_id])
                skipped_count += 1
                continue
        
        # Use Notion version (either no system modification, or Notion is newer)
        merged.append(notion_contact)
    
    if skipped_count > 0:
        logger.info(f"Conflict resolution: kept {skipped_count} system-modified contacts over Notion changes")
    
    return merged


def filter_contacts(contacts: List[dict], filter_params: ContactFilter) -> List[dict]:
    """Filter and sort contacts based on filter parameters."""
    filtered = contacts
    
    # Apply filters
    if filter_params.status:
        filtered = [c for c in filtered if c.get("status") == filter_params.status]
    
    if filter_params.type:
        filtered = [c for c in filtered if c.get("type") == filter_params.type]
    
    if filter_params.group:
        filtered = [c for c in filtered if c.get("group") == filter_params.group]
    
    if filter_params.relationship_type:
        filtered = [c for c in filtered if c.get("relationship_type") == filter_params.relationship_type]
    
    # Apply search
    if filter_params.search:
        search_term = filter_params.search.lower()
        filtered = [
            c for c in filtered
            if (search_term in (c.get("name") or "").lower() or
                search_term in (c.get("email") or "").lower() or
                search_term in (c.get("phone") or "").lower() or
                search_term in (c.get("company") or "").lower() or
                search_term in (c.get("notes") or "").lower())
        ]
    
    # Apply sorting
    sort_by = filter_params.sort_by or "name"
    sort_order = filter_params.sort_order or "asc"
    reverse = sort_order == "desc"
    
    def get_sort_value(contact, field):
        value = contact.get(field)
        if field in ["last_contact_date", "created_date"]:
            # Sort dates (None goes to end)
            return value or "9999-12-31"
        elif field == "days_at_current_status":
            return contact.get("days_at_current_status") or 0
        else:
            return (value or "").lower()
    
    try:
        filtered.sort(key=lambda c: get_sort_value(c, sort_by), reverse=reverse)
    except Exception as e:
        logger.warning(f"Error sorting contacts: {e}")
    
    return filtered


def calculate_days_at_status(contact: dict) -> int:
    """Calculate days at current status (placeholder - would need status_change_date)."""
    # For now, return the existing value or 0
    # In a full implementation, you'd track when status changed
    return contact.get("days_at_current_status", 0)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    import os
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(html_path, "r") as f:
        return HTMLResponse(
            content=f.read(),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )


@app.get("/api/contacts", response_model=List[ContactResponse])
async def get_contacts(
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, description="Filter by type"),
    group: Optional[str] = Query(None, description="Filter by group"),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: Optional[str] = Query("name", description="Sort field"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    refresh: Optional[bool] = Query(False, description="Force refresh from Notion")
):
    """Get all contacts with optional filtering and sorting."""
    try:
        # Check cache first (unless refresh is requested)
        contacts = None
        if not refresh:
            contacts = get_cached_contacts()
        
        # Fetch from Notion if cache miss or refresh requested
        if contacts is None:
            logger.info("Fetching contacts from Notion...")
            client = get_notion_client()
            notion_contacts = client.get_all_contacts()
            logger.info(f"Fetched {len(notion_contacts)} contacts from Notion")
            
            # Merge with cached contacts using conflict resolution
            cached_contacts = get_cached_contacts()
            contacts = merge_contacts_with_conflict_resolution(notion_contacts, cached_contacts)
            
            set_cached_contacts(contacts)
        
        # Apply filters
        filter_params = ContactFilter(
            status=status,
            type=type,
            group=group,
            relationship_type=relationship_type,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        filtered_contacts = filter_contacts(contacts, filter_params)
        logger.info(f"Returning {len(filtered_contacts)} filtered contacts")
        
        return filtered_contacts
    except Exception as e:
        logger.error(f"Error fetching contacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: str):
    """Get a single contact by ID."""
    try:
        client = get_notion_client()
        contact = client.get_contact(contact_id)
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        return contact
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/contacts", response_model=ContactResponse, status_code=201)
async def create_contact(contact: ContactCreate):
    """Create a new contact."""
    try:
        client = get_notion_client()
        contact_dict = contact.dict(exclude_none=True)
        created = client.create_contact(contact_dict)
        # Mark as system-modified to prevent Notion from overriding
        mark_contact_as_system_modified(created["id"])
        # Update cache with new contact
        cached = get_cached_contacts()
        if cached is not None:
            cached.append(created)
            set_cached_contacts(cached)
        else:
            invalidate_cache()  # Will refresh on next request
        return created
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: str, contact: ContactUpdate):
    """Update an existing contact."""
    try:
        client = get_notion_client()
        
        # Handle status change - reset days_at_current_status
        update_dict = contact.dict(exclude_none=True)
        if "status" in update_dict:
            # When status changes, reset days_at_current_status
            update_dict["days_at_current_status"] = 0
        
        updated = client.update_contact(contact_id, update_dict)
        # Mark as system-modified to prevent Notion from overriding
        mark_contact_as_system_modified(contact_id)
        # Update cache with updated contact
        cached = get_cached_contacts()
        if cached is not None:
            # Find and update the contact in cache
            for i, c in enumerate(cached):
                if c.get("id") == contact_id:
                    cached[i] = updated
                    break
            else:
                # Contact not in cache, add it
                cached.append(updated)
            set_cached_contacts(cached)
        else:
            invalidate_cache()  # Will refresh on next request
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/contacts/{contact_id}", status_code=204)
async def delete_contact(contact_id: str):
    """Delete (archive) a contact."""
    try:
        client = get_notion_client()
        client.delete_contact(contact_id)
        # Remove from system-modified tracking (contact is deleted)
        global _system_modified_contacts
        _system_modified_contacts.pop(contact_id, None)
        # Remove from cache
        cached = get_cached_contacts()
        if cached is not None:
            cached = [c for c in cached if c.get("id") != contact_id]
            set_cached_contacts(cached)
        else:
            invalidate_cache()  # Will refresh on next request
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        client = get_notion_client()
        # Try to query the database to verify connection
        client.get_all_contacts(page_size=1)
        return {"status": "healthy", "notion_connected": True}
    except Exception as e:
        return {"status": "unhealthy", "notion_connected": False, "error": str(e)}


# ============================================================================
# Message Endpoints
# ============================================================================

@app.post("/api/messages/send-email", response_model=MessageResponse, status_code=201)
async def send_email(message: MessageSendEmail):
    """Send an email to a contact."""
    try:
        # Get contact
        notion_client = get_notion_client()
        contact = notion_client.get_contact(message.contact_id)
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        if not contact.get("email"):
            raise HTTPException(status_code=400, detail="Contact has no email address")
        
        # Get Gmail manager
        gmail_manager = get_gmail_manager()
        if not gmail_manager:
            raise HTTPException(
                status_code=503,
                detail="Gmail integration not configured. See integrations/email/SETUP.md"
            )
        
        # Send email via Gmail (from specified account)
        # Wrap in try-except to ensure cleanup on failure
        try:
            result = gmail_manager.send_email(
                to_address=contact["email"],
                subject=message.subject,
                body=message.body,
                from_account=message.from_account
            )
        except Exception as email_error:
            # Log the error and ensure state is cleaned up
            logger.error(f"Failed to send email: {email_error}", exc_info=True)
            # Reset Gmail client state to prevent stuck state
            try:
                client = gmail_manager.get_client(message.from_account)
                if client:
                    client.reset()
            except Exception as reset_error:
                logger.warning(f"Failed to reset Gmail client: {reset_error}")
            
            # Provide helpful error messages for common OAuth issues
            error_str = str(email_error).lower()
            if 'redirect_uri_mismatch' in error_str or 'invalid_request' in error_str:
                raise HTTPException(
                    status_code=400,
                    detail=f"OAuth authentication failed: redirect_uri_mismatch. Please ensure the account '{message.from_account}' is added as a test user in Google Cloud Console OAuth consent screen, and that the redirect URI matches exactly. See integrations/email/SETUP.md for details."
                )
            elif 'access blocked' in error_str or 'invalid client' in error_str:
                raise HTTPException(
                    status_code=403,
                    detail=f"OAuth authentication failed: Access blocked. Please ensure the account '{message.from_account}' is added as a test user in Google Cloud Console OAuth consent screen. See integrations/email/SETUP.md for details."
                )
            elif 'invalid_grant' in error_str or 'token' in error_str:
                raise HTTPException(
                    status_code=401,
                    detail=f"OAuth token expired or invalid for account '{message.from_account}'. Please try again - you will be prompted to re-authenticate."
                )
            # Re-raise the original error if it's not an OAuth issue
            raise
        
        # Store message with from_account (only if email was sent successfully)
        storage = get_message_storage()
        try:
            message_create = MessageCreate(
                contact_id=message.contact_id,
                direction=MessageDirection.OUTBOUND,
                channel=MessageChannel.EMAIL,
                subject=message.subject,
                body=message.body,
                from_address=result["from_address"],
                to_address=result["to_address"],
                thread_id=result.get("thread_id"),
                provider_message_id=result.get("message_id"),
                sent_at=datetime.utcnow(),
                from_account=result.get("from_account")  # Store which account sent the email
            )
            message_record = storage.create_message(message_create)
            logger.info(f"Message saved to database: ID {message_record.id}, from_account={message_record.from_account}")
        except Exception as db_error:
            # Log the error but don't fail the request - email was already sent
            logger.error(f"Failed to save message to database: {db_error}", exc_info=True)
            # Try to retrieve the message by provider_message_id in case it was saved but the response failed
            try:
                existing = storage.get_message_by_provider_id(
                    result.get("message_id"),
                    MessageChannel.EMAIL
                )
                if existing:
                    message_record = existing
                    logger.info(f"Found existing message in database: ID {existing.id}")
                else:
                    # If we can't find it and can't save it, re-raise so we get proper error handling
                    raise db_error
            except Exception:
                # If we can't retrieve it either, re-raise the original error
                raise db_error
        
        # Update contact's last_contact_date
        try:
            notion_client.update_contact(
                message.contact_id,
                {"last_contact_date": datetime.utcnow().date().isoformat()}
            )
            mark_contact_as_system_modified(message.contact_id)
            # Update cache
            cached = get_cached_contacts()
            if cached is not None:
                for i, c in enumerate(cached):
                    if c.get("id") == message.contact_id:
                        cached[i]["last_contact_date"] = datetime.utcnow().date().isoformat()
                        break
                set_cached_contacts(cached)
            else:
                invalidate_cache()
        except Exception as e:
            logger.warning(f"Failed to update last_contact_date: {e}")
        
        # Verify message_record is valid before returning
        if not message_record or not hasattr(message_record, 'id'):
            logger.error("Invalid message record returned from storage")
            raise HTTPException(
                status_code=500,
                detail="Email sent successfully but failed to create response record."
            )
        
        return message_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        # Ensure Gmail client state is reset on any error to prevent stuck state
        try:
            gmail_manager = get_gmail_manager()
            if gmail_manager:
                gmail_manager.reset(message.from_account if hasattr(message, 'from_account') else None)
        except Exception as reset_error:
            logger.warning(f"Failed to reset Gmail client after error: {reset_error}")
        
        # Provide user-friendly error message
        error_detail = str(e)
        if not error_detail or len(error_detail) > 500:
            error_detail = "An unexpected error occurred while sending the email. Please check the server logs for details."
        
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/api/messages/send-sms", response_model=MessageResponse, status_code=201)
async def send_sms(message: MessageSendSMS):
    """Send an SMS to a contact."""
    try:
        # Get contact
        notion_client = get_notion_client()
        contact = notion_client.get_contact(message.contact_id)
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        if not contact.get("phone"):
            raise HTTPException(status_code=400, detail="Contact has no phone number")
        
        # Get Twilio client
        twilio = get_twilio_client()
        if not twilio:
            raise HTTPException(
                status_code=503,
                detail="Twilio integration not configured. See integrations/sms/SETUP.md"
            )
        
        # Normalize phone number
        to_phone = twilio.normalize_phone_number(contact["phone"])
        if not to_phone:
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        
        # Send SMS via Twilio
        result = twilio.send_sms(
            to_phone=to_phone,
            body=message.body
        )
        
        # Store message
        storage = get_message_storage()
        message_record = storage.create_message(
            MessageCreate(
                contact_id=message.contact_id,
                direction=MessageDirection.OUTBOUND,
                channel=MessageChannel.SMS,
                body=message.body,
                from_phone=result["from_phone"],
                to_phone=result["to_phone"],
                provider_message_id=result.get("message_sid"),
                sent_at=datetime.utcnow()
            )
        )
        
        # Update contact's last_contact_date
        try:
            notion_client.update_contact(
                message.contact_id,
                {"last_contact_date": datetime.utcnow().date().isoformat()}
            )
            mark_contact_as_system_modified(message.contact_id)
            # Update cache
            cached = get_cached_contacts()
            if cached is not None:
                for i, c in enumerate(cached):
                    if c.get("id") == message.contact_id:
                        cached[i]["last_contact_date"] = datetime.utcnow().date().isoformat()
                        break
                set_cached_contacts(cached)
            else:
                invalidate_cache()
        except Exception as e:
            logger.warning(f"Failed to update last_contact_date: {e}")
        
        return message_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending SMS: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/messages/sync-email")
async def sync_email():
    """Sync responses to CRM-sent emails from Gmail (filtered inbox)."""
    try:
        gmail_manager = get_gmail_manager()
        if not gmail_manager:
            raise HTTPException(
                status_code=503,
                detail="Gmail integration not configured. See integrations/email/SETUP.md"
            )
        
        storage = get_message_storage()
        notion_client = get_notion_client()
        
        # Get thread IDs from all CRM-sent emails
        crm_thread_ids = storage.get_crm_thread_ids()
        
        if not crm_thread_ids:
            return {
                "synced": 0,
                "skipped": 0,
                "total": 0,
                "message": "No CRM-sent emails found. Send an email first to create threads."
            }
        
        # Get responses to CRM-sent emails across all accounts
        gmail_messages = gmail_manager.get_crm_responses(
            thread_ids=crm_thread_ids,
            max_results=100
        )
        
        synced_count = 0
        skipped_count = 0
        
        for gmail_msg in gmail_messages:
            try:
                # Check if already synced
                provider_id = gmail_msg.get("id")
                existing = storage.get_message_by_provider_id(
                    provider_id,
                    MessageChannel.EMAIL
                )
                if existing:
                    skipped_count += 1
                    continue
                
                # Get the client for this account to parse the message
                account_email = gmail_msg.get("_account_email")
                client = gmail_manager.get_client(account_email) if account_email else None
                if not client:
                    # Fallback: try to parse without client (basic parsing)
                    headers = gmail_msg.get('payload', {}).get('headers', [])
                    def get_header(name: str) -> Optional[str]:
                        for header in headers:
                            if header['name'].lower() == name.lower():
                                return header['value']
                        return None
                    parsed = {
                        'provider_message_id': gmail_msg.get('id'),
                        'thread_id': gmail_msg.get('threadId'),
                        'from_address': get_header('From'),
                        'to_address': get_header('To'),
                        'subject': get_header('Subject'),
                        'body': "(Message body not available)",
                        'received_at': datetime.utcnow()
                    }
                else:
                    parsed = client.parse_message(gmail_msg)
                
                # Find contact by email address
                from_email = parsed.get("from_address", "")
                # Extract email from "Name <email@example.com>" format
                if "<" in from_email and ">" in from_email:
                    from_email = from_email.split("<")[1].split(">")[0]
                from_email = from_email.strip()
                
                # Get all contacts and find by email
                contacts = notion_client.get_all_contacts()
                contact = None
                for c in contacts:
                    if c.get("email") and c["email"].lower() == from_email.lower():
                        contact = c
                        break
                
                if not contact:
                    # No matching contact - skip
                    skipped_count += 1
                    continue
                
                # Store message
                storage.create_message(
                    MessageCreate(
                        contact_id=contact["id"],
                        direction=MessageDirection.INBOUND,
                        channel=MessageChannel.EMAIL,
                        subject=parsed.get("subject"),
                        body=parsed.get("body", ""),
                        from_address=parsed.get("from_address"),
                        to_address=parsed.get("to_address"),
                        thread_id=parsed.get("thread_id"),
                        provider_message_id=parsed.get("provider_message_id"),
                        received_at=parsed.get("received_at")
                    )
                )
                synced_count += 1
            except Exception as e:
                logger.warning(f"Error syncing message {gmail_msg.get('id')}: {e}")
                continue
        
        return {
            "synced": synced_count,
            "skipped": skipped_count,
            "total": len(gmail_messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/messages/inbound-sms", response_model=MessageResponse, status_code=201)
async def inbound_sms(request: Request):
    """Handle inbound SMS webhook from Twilio."""
    try:
        # Twilio sends form data, not JSON
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        twilio = get_twilio_client()
        if not twilio:
            raise HTTPException(
                status_code=503,
                detail="Twilio integration not configured. See integrations/sms/SETUP.md"
            )
        
        storage = get_message_storage()
        notion_client = get_notion_client()
        
        # Parse webhook data
        parsed = twilio.parse_inbound_webhook(webhook_data)
        
        # Check if already processed
        provider_id = parsed.get("provider_message_id")
        if provider_id:
            existing = storage.get_message_by_provider_id(
                provider_id,
                MessageChannel.SMS
            )
            if existing:
                return existing
        
        # Find contact by phone number
        from_phone = parsed.get("from_phone", "")
        normalized_from = twilio.normalize_phone_number(from_phone)
        
        # Get all contacts and find by phone
        contacts = notion_client.get_all_contacts()
        contact = None
        for c in contacts:
            if c.get("phone"):
                normalized_contact_phone = twilio.normalize_phone_number(c["phone"])
                if normalized_contact_phone and normalized_from:
                    if normalized_contact_phone == normalized_from:
                        contact = c
                        break
        
        if not contact:
            # No matching contact - still store it but without contact_id?
            # For now, raise error - you might want to handle this differently
            raise HTTPException(
                status_code=404,
                detail=f"No contact found for phone number: {from_phone}"
            )
        
        # Store message
        message_record = storage.create_message(
            MessageCreate(
                contact_id=contact["id"],
                direction=MessageDirection.INBOUND,
                channel=MessageChannel.SMS,
                body=parsed.get("body", ""),
                from_phone=parsed.get("from_phone"),
                to_phone=parsed.get("to_phone"),
                provider_message_id=parsed.get("provider_message_id"),
                received_at=parsed.get("received_at")
            )
        )
        
        return message_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling inbound SMS: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gmail/accounts")
async def get_gmail_accounts():
    """Get list of configured Gmail accounts."""
    try:
        gmail_manager = get_gmail_manager()
        if not gmail_manager:
            return {"accounts": []}
        
        accounts = gmail_manager.get_all_accounts()
        return {"accounts": accounts}
    except Exception as e:
        logger.error(f"Error getting Gmail accounts: {e}", exc_info=True)
        return {"accounts": []}


@app.post("/api/gmail/reset")
async def reset_gmail_client(account_email: Optional[str] = None):
    """
    Reset Gmail client state for a specific account or all accounts.
    Useful for clearing stuck states after errors.
    
    Args:
        account_email: Optional email address to reset (if None, resets all accounts)
    """
    try:
        gmail_manager = get_gmail_manager()
        if not gmail_manager:
            raise HTTPException(
                status_code=503,
                detail="Gmail integration not configured. See integrations/email/SETUP.md"
            )
        
        gmail_manager.reset(account_email)
        
        if account_email:
            return {"status": "success", "message": f"Reset Gmail client for account: {account_email}"}
        else:
            return {"status": "success", "message": "Reset all Gmail clients"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting Gmail client: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/messages", response_model=List[MessageResponse])
async def get_messages(
    contact_id: Optional[str] = Query(None, description="Filter by contact ID"),
    channel: Optional[str] = Query(None, description="Filter by channel (email, sms)"),
    direction: Optional[str] = Query(None, description="Filter by direction (inbound, outbound)"),
    crm_sent_only: Optional[bool] = Query(False, description="Only show emails sent from CRM (for outbox)"),
    crm_responses_only: Optional[bool] = Query(False, description="Only show responses to CRM-sent emails (for inbox)"),
    limit: Optional[int] = Query(100, description="Maximum number of messages")
):
    """Get messages with optional filtering (supports inbox/outbox views)."""
    try:
        storage = get_message_storage()
        
        # Build filter
        filter_params = MessageFilter(
            contact_id=contact_id,
            channel=MessageChannel(channel) if channel else None,
            direction=MessageDirection(direction) if direction else None,
            crm_sent_only=crm_sent_only,
            crm_responses_only=crm_responses_only,
            limit=limit
        )
        
        messages = storage.get_messages(filter_params)
        return messages
    except Exception as e:
        logger.error(f"Error getting messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contacts/{contact_id}/messages", response_model=List[MessageResponse])
async def get_contact_messages(
    contact_id: str,
    channel: Optional[str] = Query(None, description="Filter by channel (email, sms)"),
    direction: Optional[str] = Query(None, description="Filter by direction (inbound, outbound)"),
    crm_sent_only: Optional[bool] = Query(False, description="Only show emails sent from CRM"),
    crm_responses_only: Optional[bool] = Query(False, description="Only show responses to CRM-sent emails"),
    limit: Optional[int] = Query(100, description="Maximum number of messages")
):
    """Get all messages for a contact."""
    try:
        # Verify contact exists
        notion_client = get_notion_client()
        contact = notion_client.get_contact(contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Build filter
        filter_params = MessageFilter(
            contact_id=contact_id,
            channel=MessageChannel(channel) if channel else None,
            direction=MessageDirection(direction) if direction else None,
            crm_sent_only=crm_sent_only,
            crm_responses_only=crm_responses_only,
            limit=limit
        )
        
        if channel:
            try:
                filter_params.channel = MessageChannel(channel.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}")
        
        if direction:
            try:
                filter_params.direction = MessageDirection(direction.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid direction: {direction}")
        
        # Get messages
        storage = get_message_storage()
        messages = storage.get_messages(filter_params)
        
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages for contact {contact_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
