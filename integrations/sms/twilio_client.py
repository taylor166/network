"""
Twilio SMS integration client.

Handles SMS sending and receiving via Twilio API.
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime
import logging

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioException
except ImportError:
    # Will be caught during initialization
    pass

logger = logging.getLogger(__name__)


class TwilioSMSClient:
    """Client for Twilio SMS operations."""
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None
    ):
        """
        Initialize Twilio client.
        
        Args:
            account_sid: Twilio Account SID (or from env TWILIO_ACCOUNT_SID)
            auth_token: Twilio Auth Token (or from env TWILIO_AUTH_TOKEN)
            from_number: Twilio phone number to send from (or from env TWILIO_FROM_NUMBER)
        """
        try:
            from twilio.rest import Client as TwilioClient
        except ImportError:
            raise ImportError(
                "Twilio dependencies not installed. Install with: pip install twilio"
            )
        
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER")
        
        if not self.account_sid or not self.auth_token:
            raise ValueError(
                "Twilio credentials required. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN "
                "environment variables or pass them to TwilioSMSClient."
            )
        
        if not self.from_number:
            raise ValueError(
                "Twilio from number required. Set TWILIO_FROM_NUMBER environment variable "
                "or pass it to TwilioSMSClient."
            )
        
        try:
            self.client = TwilioClient(self.account_sid, self.auth_token)
        except Exception as e:
            logger.error(f"Error initializing Twilio client: {e}")
            raise
    
    def send_sms(
        self,
        to_phone: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Send an SMS via Twilio.
        
        Args:
            to_phone: Recipient phone number (E.164 format, e.g., +1234567890)
            body: SMS body text
        
        Returns:
            Dictionary with message_sid and other details
        """
        try:
            message = self.client.messages.create(
                body=body,
                from_=self.from_number,
                to=to_phone
            )
            
            logger.info(f"SMS sent successfully. Message SID: {message.sid}")
            
            return {
                'message_sid': message.sid,
                'status': message.status,
                'from_phone': self.from_number,
                'to_phone': to_phone,
                'date_sent': message.date_sent
            }
        except TwilioException as e:
            logger.error(f"Twilio API error sending SMS: {e}")
            raise Exception(f"Failed to send SMS: {e}")
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            raise
    
    def parse_inbound_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Twilio webhook data into our message format.
        
        Args:
            webhook_data: Twilio webhook POST data
        
        Returns:
            Dictionary with parsed message data
        """
        return {
            'provider_message_id': webhook_data.get('MessageSid'),
            'from_phone': webhook_data.get('From'),
            'to_phone': webhook_data.get('To'),
            'body': webhook_data.get('Body', ''),
            'received_at': datetime.utcnow()  # Twilio provides timestamp, but we'll use current time
        }
    
    def validate_phone_number(self, phone: str) -> bool:
        """
        Basic phone number validation (E.164 format).
        
        Args:
            phone: Phone number to validate
        
        Returns:
            True if valid format
        """
        # Basic E.164 format check: starts with +, followed by digits
        if not phone:
            return False
        if not phone.startswith('+'):
            return False
        if len(phone) < 8 or len(phone) > 15:  # E.164 max length
            return False
        if not phone[1:].isdigit():
            return False
        return True
    
    def normalize_phone_number(self, phone: str) -> Optional[str]:
        """
        Normalize phone number to E.164 format.
        
        This is a basic implementation. For production, use a library like phonenumbers.
        
        Args:
            phone: Phone number to normalize
        
        Returns:
            Normalized phone number or None if invalid
        """
        if not phone:
            return None
        
        # Remove all non-digit characters except +
        normalized = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # If doesn't start with +, try to add country code (US default: +1)
        if not normalized.startswith('+'):
            # Assume US number if 10 digits
            if len(normalized) == 10:
                normalized = '+1' + normalized
            else:
                # Try to add + if it looks like it might be missing
                normalized = '+' + normalized
        
        # Basic validation
        if self.validate_phone_number(normalized):
            return normalized
        
        return None
