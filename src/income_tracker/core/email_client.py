"""Email client for handling IMAP connections and email retrieval."""

import email
import imaplib
import logging
from contextlib import contextmanager
from email.header import decode_header
from email.message import EmailMessage
from typing import Generator

logger = logging.getLogger(__name__)


class EmailConnectionError(Exception):
    """Raised when email connection fails."""


class EmailClient:
    """IMAP email client for retrieving payment notifications."""
    
    def __init__(self, email_address: str, email_password: str, server: str = "imap.gmail.com") -> None:
        """Initialize email client with credentials.
        
        Args:
            email_address: Email address for IMAP connection
            email_password: App password for email account  
            server: IMAP server hostname
        """
        self.email_address = email_address
        self.email_password = email_password
        self.server = server
        self._validate_credentials()
    
    def _validate_credentials(self) -> None:
        """Validate that credentials are provided."""
        if not self.email_address or not self.email_password:
            raise ValueError("Email address and password must be provided")
    
    @contextmanager
    def connection(self) -> Generator[imaplib.IMAP4_SSL, None, None]:
        """Context manager for IMAP connection."""
        mail = None
        try:
            mail = imaplib.IMAP4_SSL(self.server)
            mail.login(self.email_address, self.email_password)
            logger.info(f"Connected to {self.server} as {self.email_address}")
            yield mail
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            raise EmailConnectionError(f"Email connection failed: {e}") from e
        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except Exception as e:
                    logger.warning(f"Error closing email connection: {e}")
    
    def search_emails(self, sender: str) -> list[bytes]:
        """Search for emails from specific sender.
        
        Args:
            sender: Email address to search for
            
        Returns:
            List of email IDs
        """
        with self.connection() as mail:
            mail.select('inbox')
            status, messages = mail.search(None, f'(FROM "{sender}")')
            if status != 'OK':
                logger.warning(f"Failed to search emails from {sender}")
                return []
            return messages[0].split()
    
    def fetch_email(self, email_id: bytes) -> EmailMessage | None:
        """Fetch and parse email by ID.
        
        Args:
            email_id: Email ID to fetch
            
        Returns:
            Parsed email message or None if failed
        """
        with self.connection() as mail:
            mail.select('inbox')
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK' or not msg_data[0]:
                    return None
                
                email_body = msg_data[0][1]
                return email.message_from_bytes(email_body)
            except Exception as e:
                logger.error(f"Error fetching email {email_id}: {e}")
                return None
    
    @staticmethod
    def decode_subject(email_message: EmailMessage) -> str:
        """Decode email subject handling encoding."""
        subject = email_message.get("Subject", "")
        if not subject:
            return ""
        
        decoded = decode_header(subject)[0][0]
        if isinstance(decoded, bytes):
            return decoded.decode()
        return str(decoded)
    
    @staticmethod
    def extract_body(email_message: EmailMessage) -> str:
        """Extract plain text body from email message."""
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode()
                        break
        else:
            payload = email_message.get_payload(decode=True)
            if payload:
                body = payload.decode()
        return body
