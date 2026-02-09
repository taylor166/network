"""
FastAPI endpoints for contact management.
"""
from fastapi import FastAPI, HTTPException, Query
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

# Simple in-memory cache for contacts
_contacts_cache = None
_cache_timestamp = None
_cache_ttl = 60  # Cache for 60 seconds

def get_notion_client() -> NotionContactClient:
    """Get or create Notion client instance."""
    global notion_client
    if notion_client is None:
        notion_client = NotionContactClient()
    return notion_client

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
            contacts = client.get_all_contacts()
            logger.info(f"Fetched {len(contacts)} contacts from Notion")
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
        invalidate_cache()  # Invalidate cache after creating contact
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
        invalidate_cache()  # Invalidate cache after updating contact
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
        invalidate_cache()  # Invalidate cache after deleting contact
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
