"""
Gmail API integration client.

Handles OAuth authentication and email sending/receiving via Gmail API.
"""
import os
import base64
import json
import socket
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    # Will be caught during initialization
    pass

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']


class GmailClient:
    """Client for Gmail API operations with multi-account support."""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        token_file: Optional[str] = None,
        account_email: Optional[str] = None
    ):
        """
        Initialize Gmail client for a specific account.
        
        Args:
            client_id: Gmail OAuth client ID (or from env GMAIL_CLIENT_ID)
            client_secret: Gmail OAuth client secret (or from env GMAIL_CLIENT_SECRET)
            redirect_uri: OAuth redirect URI (or from env GMAIL_REDIRECT_URI)
            token_file: Path to token file (defaults to integrations/email/token_{account_email}.json)
            account_email: Email address for this account (used for token file naming)
        """
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "Gmail API dependencies not installed. Install with: "
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        
        self.client_id = client_id or os.getenv("GMAIL_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GMAIL_CLIENT_SECRET")
        # Default to http://localhost:8080/ for OAuth callback (fixed port for Google registration)
        self.redirect_uri = redirect_uri or os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8080/")
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Gmail OAuth credentials required. Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET "
                "environment variables or pass them to GmailClient."
            )
        
        # Store account email for identification
        self.account_email = account_email
        
        # Token file path - use account-specific token file
        if token_file:
            self.token_file = token_file
        else:
            token_dir = os.path.join(os.path.dirname(__file__))
            os.makedirs(token_dir, exist_ok=True)
            if account_email:
                # Use account email in filename (sanitized)
                safe_email = account_email.replace("@", "_").replace(".", "_")
                self.token_file = os.path.join(token_dir, f"token_{safe_email}.json")
            else:
                self.token_file = os.path.join(token_dir, "token.json")
        
        # Credentials file path (for OAuth flow)
        creds_dir = os.path.join(os.path.dirname(__file__))
        self.credentials_file = os.path.join(creds_dir, "credentials.json")
        
        self.service = None
        self.credentials = None
        # Lock to prevent concurrent OAuth flows
        self._oauth_lock = threading.Lock()
    
    def _find_available_port(self, preferred_port: int, exclude: Optional[List[int]] = None) -> int:
        """
        Find an available port, starting with the preferred port.
        
        Args:
            preferred_port: The preferred port to use
            exclude: List of ports to exclude from consideration
        
        Returns:
            An available port number
        """
        exclude = exclude or []
        
        # Check if preferred port is available
        if preferred_port not in exclude and self._is_port_available(preferred_port):
            return preferred_port
        
        # Try nearby ports (preferred_port ± 1, ± 2, etc.)
        for offset in range(1, 100):
            for port in [preferred_port + offset, preferred_port - offset]:
                if port > 0 and port < 65536 and port not in exclude:
                    if self._is_port_available(port):
                        logger.info(f"Using alternative port {port} (preferred {preferred_port} was unavailable)")
                        return port
        
        # Fallback: let the system assign a port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            port = s.getsockname()[1]
            logger.info(f"System assigned port {port}")
            return port
    
    def _is_port_available(self, port: int) -> bool:
        """
        Check if a port is available.
        
        Args:
            port: Port number to check
        
        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    def _get_credentials(self) -> 'Credentials':
        """Get valid user credentials from storage or OAuth flow."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                logger.warning(f"Error loading token: {e}")
        
        # If there are no (valid) credentials available, start OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired token
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                # Start OAuth flow - use lock to prevent concurrent flows
                with self._oauth_lock:
                    # Double-check credentials weren't created by another thread
                    if os.path.exists(self.token_file):
                        try:
                            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                            if creds and creds.valid:
                                return creds
                        except Exception:
                            pass
                    
                    # Log why OAuth flow is being triggered
                    if not os.path.exists(self.token_file):
                        logger.warning(f"No token file found at {self.token_file}. Starting OAuth flow for initial authentication.")
                    else:
                        logger.warning(f"Token file exists but credentials are invalid. Starting OAuth flow to re-authenticate.")
                    
                    if not os.path.exists(self.credentials_file):
                        # Create credentials.json from environment variables
                        self._create_credentials_file()
                    
                    # Extract port from redirect_uri if specified, otherwise use default 8080
                    # For desktop apps, Google allows http://localhost or http://127.0.0.1
                    # We'll use a fixed port to match what's registered in Google Cloud Console
                    import re
                    port_match = re.search(r':(\d+)', self.redirect_uri)
                    if port_match:
                        preferred_port = int(port_match.group(1))
                    else:
                        # Default to 8080 if no port specified
                        preferred_port = 8080
                    
                    # Find an available port (try preferred port first, then try nearby ports)
                    oauth_port = self._find_available_port(preferred_port)
                    
                    # Use http://localhost for redirect (Google allows this for desktop apps)
                    # The actual redirect will be to the port we specify
                    redirect_base = "http://localhost"
                    
                    flow = InstalledAppFlow.from_client_config(
                        {
                            "installed": {
                                "client_id": self.client_id,
                                "client_secret": self.client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [f"{redirect_base}:{oauth_port}/"],
                            }
                        },
                        SCOPES
                    )
                    
                    # Try to run the OAuth server, handling port conflicts gracefully
                    try:
                        logger.info(f"Starting OAuth flow on port {oauth_port}...")
                        creds = flow.run_local_server(port=oauth_port, open_browser=True)
                    except OSError as e:
                        if e.errno == 48:  # Address already in use
                            # Try to find another available port
                            logger.warning(f"Port {oauth_port} is in use, trying alternative port...")
                            oauth_port = self._find_available_port(preferred_port, exclude=[oauth_port])
                            # Update redirect URI in flow config
                            flow = InstalledAppFlow.from_client_config(
                                {
                                    "installed": {
                                        "client_id": self.client_id,
                                        "client_secret": self.client_secret,
                                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                        "token_uri": "https://oauth2.googleapis.com/token",
                                        "redirect_uris": [f"{redirect_base}:{oauth_port}/"],
                                    }
                                },
                                SCOPES
                            )
                            logger.info(f"Retrying OAuth flow on alternative port {oauth_port}...")
                            creds = flow.run_local_server(port=oauth_port, open_browser=True)
                        else:
                            # Reset state on OAuth failure to prevent stuck state
                            self.reset()
                            raise
                    except Exception as e:
                        # Reset state on any OAuth failure to prevent stuck state
                        logger.error(f"OAuth flow failed: {e}")
                        self.reset()
                        raise
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    def _create_credentials_file(self):
        """Create credentials.json file from environment variables."""
        credentials_data = {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri],
            }
        }
        with open(self.credentials_file, 'w') as f:
            json.dump(credentials_data, f, indent=2)
    
    def reset(self):
        """
        Reset the client state - clear cached service and credentials.
        Useful when credentials become invalid or need to be refreshed.
        """
        logger.info("Resetting Gmail client state")
        self.service = None
        self.credentials = None
    
    def _get_service(self):
        """Get Gmail API service instance."""
        if not self.service:
            self.credentials = self._get_credentials()
            self.service = build('gmail', 'v1', credentials=self.credentials)
        return self.service
    
    def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        from_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail API.
        
        Args:
            to_address: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_address: Sender email (optional, uses authenticated user's email)
        
        Returns:
            Dictionary with message_id, thread_id, and from_address
        """
        try:
            service = self._get_service()
            
            # Get user's email if not provided
            if not from_address:
                profile = service.users().getProfile(userId='me').execute()
                from_address = profile['emailAddress']
            
            # Create message
            message = MIMEText(body)
            message['to'] = to_address
            message['from'] = from_address
            message['subject'] = subject
            
            # Add X-CRM-Sent header to identify CRM-sent emails
            message['X-CRM-Sent'] = 'true'
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            send_result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            message_id = send_result.get('id')
            thread_id = send_result.get('threadId')
            
            logger.info(f"Email sent successfully from {from_address}. Message ID: {message_id}, Thread ID: {thread_id}")
            
            return {
                'message_id': message_id,
                'thread_id': thread_id,
                'from_address': from_address,
                'to_address': to_address
            }
        except HttpError as error:
            # Check if it's an authentication error - reset state if so
            if error.resp.status in [401, 403]:
                logger.warning(f"Authentication error ({error.resp.status}), resetting client state")
                self.reset()
            logger.error(f"Gmail API error sending email: {error}")
            raise Exception(f"Failed to send email: {error}")
        except Exception as e:
            # Check if it's a credential-related error - reset state if so
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['credential', 'authentication', 'unauthorized', 'invalid token']):
                logger.warning(f"Credential error detected, resetting client state: {e}")
                self.reset()
            logger.error(f"Error sending email: {e}")
            raise
    
    def get_account_email(self) -> Optional[str]:
        """Get the email address for this account."""
        try:
            service = self._get_service()
            profile = service.users().getProfile(userId='me').execute()
            return profile['emailAddress']
        except Exception as e:
            logger.warning(f"Could not get account email: {e}")
            return self.account_email
    
    def get_recent_messages(
        self,
        max_results: int = 50,
        query: Optional[str] = None,
        crm_sent_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from Gmail.
        
        Args:
            max_results: Maximum number of messages to retrieve
            query: Gmail search query (e.g., "is:unread", "from:example@gmail.com")
            crm_sent_only: If True, only return messages sent from CRM (has X-CRM-Sent header)
        
        Returns:
            List of message dictionaries with id, threadId, snippet, etc.
        """
        try:
            service = self._get_service()
            
            # Build query - add filter for CRM-sent emails if requested
            if crm_sent_only:
                # Search for emails with X-CRM-Sent header
                # Note: Gmail search doesn't directly support custom headers, so we'll filter after fetching
                base_query = query or ""
            else:
                base_query = query or ""
            
            query_params = {
                'userId': 'me',
                'maxResults': max_results * 2 if crm_sent_only else max_results  # Fetch more to filter
            }
            if base_query:
                query_params['q'] = base_query
            
            # List messages
            results = service.users().messages().list(**query_params).execute()
            messages = results.get('messages', [])
            
            # Get full message details
            full_messages = []
            for msg in messages:
                try:
                    full_msg = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Filter for CRM-sent emails if requested
                    if crm_sent_only:
                        headers = full_msg.get('payload', {}).get('headers', [])
                        has_crm_header = any(
                            h.get('name', '').lower() == 'x-crm-sent' 
                            for h in headers
                        )
                        if not has_crm_header:
                            continue
                    
                    full_messages.append(full_msg)
                    
                    # Stop if we have enough filtered results
                    if len(full_messages) >= max_results:
                        break
                except Exception as e:
                    logger.warning(f"Error fetching message {msg['id']}: {e}")
                    continue
            
            return full_messages
        except HttpError as error:
            logger.error(f"Gmail API error fetching messages: {error}")
            raise Exception(f"Failed to fetch messages: {error}")
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            raise
    
    def get_responses_to_crm_emails(
        self,
        thread_ids: List[str],
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get responses to emails sent from CRM (by thread IDs).
        
        Args:
            thread_ids: List of thread IDs from CRM-sent emails
            max_results: Maximum number of messages to retrieve
        
        Returns:
            List of message dictionaries that are responses to CRM-sent emails
        """
        if not thread_ids:
            return []
        
        try:
            service = self._get_service()
            
            # Get messages from these threads
            all_messages = []
            for thread_id in thread_ids[:10]:  # Limit to avoid too many API calls
                try:
                    thread = service.users().threads().get(
                        userId='me',
                        id=thread_id,
                        format='full'
                    ).execute()
                    
                    messages = thread.get('messages', [])
                    for msg in messages:
                        # Check if this is a reply (not the original sent message)
                        headers = msg.get('payload', {}).get('headers', [])
                        has_crm_header = any(
                            h.get('name', '').lower() == 'x-crm-sent' 
                            for h in headers
                        )
                        # Only include if it's NOT a CRM-sent message (i.e., it's a response)
                        if not has_crm_header:
                            all_messages.append(msg)
                except Exception as e:
                    logger.warning(f"Error fetching thread {thread_id}: {e}")
                    continue
            
            # Sort by date (newest first) and limit
            all_messages.sort(
                key=lambda m: int(m.get('internalDate', 0)),
                reverse=True
            )
            
            return all_messages[:max_results]
        except HttpError as error:
            logger.error(f"Gmail API error fetching responses: {error}")
            raise Exception(f"Failed to fetch responses: {error}")
        except Exception as e:
            logger.error(f"Error fetching responses: {e}")
            raise
    
    def parse_message(self, gmail_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Gmail message into our message format.
        
        Args:
            gmail_message: Gmail API message object
        
        Returns:
            Dictionary with parsed message data
        """
        headers = gmail_message.get('payload', {}).get('headers', [])
        
        def get_header(name: str) -> Optional[str]:
            for header in headers:
                if header['name'].lower() == name.lower():
                    return header['value']
            return None
        
        # Extract email addresses
        from_address = get_header('From')
        to_address = get_header('To')
        subject = get_header('Subject')
        
        # Extract body
        body = self._extract_body(gmail_message.get('payload', {}))
        
        # Extract dates
        date_str = get_header('Date')
        received_at = None
        if date_str:
            try:
                from email.utils import parsedate_to_datetime
                from datetime import timezone
                received_at = parsedate_to_datetime(date_str)
                # Convert to UTC if timezone-aware, otherwise assume UTC
                if received_at.tzinfo is None:
                    received_at = received_at.replace(tzinfo=timezone.utc)
                else:
                    received_at = received_at.astimezone(timezone.utc)
                # Remove timezone for storage (we'll store as naive UTC)
                received_at = received_at.replace(tzinfo=None)
            except Exception as e:
                logger.warning(f"Error parsing date {date_str}: {e}")
                received_at = datetime.utcnow()
        
        return {
            'provider_message_id': gmail_message.get('id'),
            'thread_id': gmail_message.get('threadId'),
            'from_address': from_address,
            'to_address': to_address,
            'subject': subject,
            'body': body,
            'received_at': received_at or datetime.utcnow()
        }
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract text body from Gmail message payload."""
        body = ""
        
        # Check if body is directly in payload
        if 'body' in payload and 'data' in payload['body']:
            try:
                body_data = payload['body']['data']
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
            except:
                pass
        
        # Check parts (for multipart messages)
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if 'body' in part and 'data' in part['body']:
                        try:
                            body_data = part['body']['data']
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            break
                        except:
                            pass
                elif part.get('mimeType') == 'text/html' and not body:
                    # Fallback to HTML if no plain text
                    if 'body' in part and 'data' in part['body']:
                        try:
                            body_data = part['body']['data']
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            # Strip HTML tags (basic)
                            import re
                            body = re.sub(r'<[^>]+>', '', body)
                            break
                        except:
                            pass
        
        return body or "(No body content)"


class MultiAccountGmailManager:
    """Manager for multiple Gmail accounts."""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        account_emails: Optional[List[str]] = None
    ):
        """
        Initialize multi-account Gmail manager.
        
        Args:
            client_id: Gmail OAuth client ID
            client_secret: Gmail OAuth client secret
            redirect_uri: OAuth redirect URI
            account_emails: List of account emails to manage (defaults to env GMAIL_ACCOUNTS)
        """
        self.client_id = client_id or os.getenv("GMAIL_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GMAIL_CLIENT_SECRET")
        # Default to http://localhost:8080/ for OAuth callback (fixed port for Google registration)
        self.redirect_uri = redirect_uri or os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8080/")
        
        # Get account emails from env or parameter
        if account_emails:
            self.account_emails = account_emails
        else:
            accounts_env = os.getenv("GMAIL_ACCOUNTS", "")
            if accounts_env:
                self.account_emails = [email.strip() for email in accounts_env.split(",") if email.strip()]
            else:
                self.account_emails = []
        
        # Initialize clients for each account
        self.clients: Dict[str, GmailClient] = {}
        for email in self.account_emails:
            try:
                self.clients[email] = GmailClient(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    account_email=email
                )
            except Exception as e:
                logger.warning(f"Could not initialize Gmail client for {email}: {e}")
    
    def get_client(self, account_email: Optional[str] = None) -> Optional[GmailClient]:
        """
        Get Gmail client for a specific account.
        
        Args:
            account_email: Email address of the account (if None, returns first available)
        
        Returns:
            GmailClient instance or None
        """
        if account_email:
            return self.clients.get(account_email)
        elif self.clients:
            # Return first available client
            return next(iter(self.clients.values()))
        return None
    
    def reset(self, account_email: Optional[str] = None):
        """
        Reset Gmail client state for a specific account or all accounts.
        
        Args:
            account_email: Email address of the account to reset (if None, resets all accounts)
        """
        if account_email:
            client = self.clients.get(account_email)
            if client:
                client.reset()
                logger.info(f"Reset Gmail client for account: {account_email}")
        else:
            # Reset all clients
            for email, client in self.clients.items():
                try:
                    client.reset()
                    logger.info(f"Reset Gmail client for account: {email}")
                except Exception as e:
                    logger.warning(f"Failed to reset client for {email}: {e}")
    
    def get_all_accounts(self) -> List[str]:
        """Get list of all configured account emails."""
        return list(self.clients.keys())
    
    def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        from_account: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email from a specific account.
        
        Args:
            to_address: Recipient email
            subject: Email subject
            body: Email body
            from_account: Account email to send from (if None, uses first available)
        
        Returns:
            Dictionary with message details including from_address
        """
        client = self.get_client(from_account)
        if not client:
            raise ValueError(f"No Gmail client available for account: {from_account or 'default'}")
        
        result = client.send_email(to_address, subject, body)
        result['from_account'] = result['from_address']  # Store which account sent it
        return result
    
    def get_crm_sent_emails(
        self,
        max_results: int = 50,
        account_email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get emails sent from CRM across all accounts or a specific account.
        
        Args:
            max_results: Maximum results per account
            account_email: Specific account to query (None for all accounts)
        
        Returns:
            List of message dictionaries
        """
        all_messages = []
        
        accounts_to_query = [account_email] if account_email else self.get_all_accounts()
        
        for email in accounts_to_query:
            client = self.get_client(email)
            if not client:
                continue
            
            try:
                messages = client.get_recent_messages(
                    max_results=max_results,
                    crm_sent_only=True
                )
                # Add account email to each message
                for msg in messages:
                    msg['_account_email'] = email
                all_messages.extend(messages)
            except Exception as e:
                logger.warning(f"Error fetching CRM-sent emails from {email}: {e}")
        
        # Sort by date (newest first)
        all_messages.sort(
            key=lambda m: int(m.get('internalDate', 0)),
            reverse=True
        )
        
        return all_messages[:max_results]
    
    def get_crm_responses(
        self,
        thread_ids: List[str],
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get responses to CRM-sent emails across all accounts.
        
        Args:
            thread_ids: List of thread IDs from CRM-sent emails
            max_results: Maximum number of responses to return
        
        Returns:
            List of response message dictionaries
        """
        all_responses = []
        
        for email, client in self.clients.items():
            try:
                responses = client.get_responses_to_crm_emails(thread_ids, max_results)
                # Add account email to each response
                for msg in responses:
                    msg['_account_email'] = email
                all_responses.extend(responses)
            except Exception as e:
                logger.warning(f"Error fetching responses from {email}: {e}")
        
        # Sort by date (newest first)
        all_responses.sort(
            key=lambda m: int(m.get('internalDate', 0)),
            reverse=True
        )
        
        return all_responses[:max_results]
