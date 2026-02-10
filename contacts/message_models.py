"""
Pydantic models for message data validation.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class MessageDirection(str, Enum):
    """Message direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageChannel(str, Enum):
    """Message channel."""
    EMAIL = "email"
    SMS = "sms"


class MessageBase(BaseModel):
    """Base message model with common fields."""
    contact_id: str = Field(..., description="Contact ID (Notion page ID)")
    direction: MessageDirection = Field(..., description="Message direction")
    channel: MessageChannel = Field(..., description="Message channel")
    body: str = Field(..., description="Message body/content")
    subject: Optional[str] = Field(None, description="Email subject (for email only)")
    from_address: Optional[str] = Field(None, description="From email address")
    to_address: Optional[str] = Field(None, description="To email address")
    from_phone: Optional[str] = Field(None, description="From phone number")
    to_phone: Optional[str] = Field(None, description="To phone number")
    thread_id: Optional[str] = Field(None, description="Email thread ID or conversation ID")
    provider_message_id: Optional[str] = Field(None, description="Provider message ID (Gmail/Twilio)")
    
    @validator("subject")
    def validate_subject_for_email(cls, v, values):
        """Subject should be provided for email messages."""
        if values.get("channel") == MessageChannel.EMAIL and not v:
            # Allow empty subject for inbound emails (they might not have one)
            pass
        return v
    
    @validator("from_address", "to_address")
    def validate_email_addresses(cls, v, values):
        """Email addresses should be provided for email messages."""
        if values.get("channel") == MessageChannel.EMAIL:
            # Validation happens at API level
            pass
        return v
    
    @validator("from_phone", "to_phone")
    def validate_phone_numbers(cls, v, values):
        """Phone numbers should be provided for SMS messages."""
        if values.get("channel") == MessageChannel.SMS:
            # Validation happens at API level
            pass
        return v


class MessageCreate(MessageBase):
    """Model for creating a new message."""
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp (for outbound)")
    received_at: Optional[datetime] = Field(None, description="Received timestamp (for inbound)")
    from_account: Optional[str] = Field(None, description="Account email that sent the message (for CRM tracking)")


class MessageResponse(MessageBase):
    """Model for message response (includes ID and timestamps)."""
    id: int = Field(..., description="Message ID")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    received_at: Optional[datetime] = Field(None, description="Received timestamp")
    created_at: datetime = Field(..., description="Created timestamp")
    from_account: Optional[str] = Field(None, description="Account email that sent the message (for CRM tracking)")
    
    class Config:
        from_attributes = True


class MessageSendEmail(BaseModel):
    """Model for sending an email."""
    contact_id: str = Field(..., description="Contact ID")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    from_account: Optional[str] = Field(None, description="Account email to send from (taylor@mavnox.com or taylorjwalshe@gmail.com)")


class MessageSendSMS(BaseModel):
    """Model for sending an SMS."""
    contact_id: str = Field(..., description="Contact ID")
    body: str = Field(..., description="SMS body")


class MessageFilter(BaseModel):
    """Model for filtering messages."""
    contact_id: Optional[str] = None
    channel: Optional[MessageChannel] = None
    direction: Optional[MessageDirection] = None
    crm_sent_only: Optional[bool] = Field(False, description="Only show emails sent from CRM (for outbox)")
    crm_responses_only: Optional[bool] = Field(False, description="Only show responses to CRM-sent emails (for inbox)")
    limit: Optional[int] = Field(100, description="Maximum number of messages to return")
    offset: Optional[int] = Field(0, description="Offset for pagination")
