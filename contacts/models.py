"""
Pydantic models for contact data validation.
"""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, validator


class ContactBase(BaseModel):
    """Base contact model with common fields."""
    name: str = Field(..., description="Full name (required)")
    email: Optional[str] = Field(None, description="Primary email")
    phone: Optional[str] = Field(None, description="Primary phone")
    status: Optional[str] = Field("queued", description="Contact status")
    type: Optional[str] = Field(None, description="Contact type (existing, 2026_new)")
    group: Optional[str] = Field(None, description="Relationship group")
    relationship_type: Optional[str] = Field(None, description="Relationship type")
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    industry: Optional[str] = Field(None, description="Industry")
    location: Optional[str] = Field(None, description="Location")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn URL")
    notes: Optional[str] = Field(None, description="Free-form notes")
    last_contact_date: Optional[str] = Field(None, description="Last contact date (ISO format)")
    call_count: Optional[int] = Field(0, description="Number of calls")
    days_at_current_status: Optional[int] = Field(0, description="Days at current status")
    next_followup_date: Optional[str] = Field(None, description="Next follow-up date (ISO format)")
    followup_context: Optional[str] = Field(None, description="Follow-up context/notes")
    
    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    @validator("status")
    def validate_status(cls, v):
        valid_statuses = [
            "wait", "queued", "need_to_contact", "contacted",
            "circle_back", "scheduled", "done", "ghosted"
        ]
        if v and v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v
    
    @validator("type")
    def validate_type(cls, v):
        if v and v not in ["existing", "2026_new"]:
            raise ValueError("Type must be 'existing' or '2026_new'")
        return v
    
    @validator("relationship_type")
    def validate_relationship_type(cls, v):
        if v and v not in ["friend", "advisor", "potential_client", "colleague", "other"]:
            raise ValueError("Relationship type must be one of: friend, advisor, potential_client, colleague, other")
        return v


class ContactCreate(ContactBase):
    """Model for creating a new contact."""
    pass
    
    @validator("email", "phone", always=True)
    def at_least_one_contact_method(cls, v, values):
        email = values.get("email")
        phone = values.get("phone")
        if not email and not phone:
            raise ValueError("At least one of email or phone is required")
        return v


class ContactUpdate(BaseModel):
    """Model for updating a contact (all fields optional)."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    group: Optional[str] = None
    relationship_type: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    last_contact_date: Optional[str] = None
    call_count: Optional[int] = None
    days_at_current_status: Optional[int] = None
    next_followup_date: Optional[str] = None
    followup_context: Optional[str] = None


class ContactResponse(ContactBase):
    """Model for contact response (includes ID and timestamps)."""
    id: str = Field(..., description="Notion page ID")
    created_date: Optional[str] = Field(None, description="Creation date (ISO format)")
    
    class Config:
        from_attributes = True


class ContactFilter(BaseModel):
    """Model for filtering contacts."""
    status: Optional[str] = None
    type: Optional[str] = None
    group: Optional[str] = None
    relationship_type: Optional[str] = None
    search: Optional[str] = Field(None, description="Search in name, email, phone, company, notes")
    sort_by: Optional[str] = Field("name", description="Sort field: name, last_contact_date, days_at_current_status")
    sort_order: Optional[str] = Field("asc", description="Sort order: asc or desc")
