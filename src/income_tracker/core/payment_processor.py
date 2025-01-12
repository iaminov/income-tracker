"""Payment processor for extracting and validating payment information from emails."""

import re
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
from email import utils as email_utils

from ..models import PaymentRecord, PaymentPattern, PaymentSource

logger = logging.getLogger(__name__)


class PaymentProcessorError(Exception):
    """Raised when payment processing fails."""


class PaymentProcessor:
    """Processes emails to extract payment information."""
    
    def __init__(self) -> None:
        """Initialize payment processor with service patterns."""
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> dict[PaymentSource, PaymentPattern]:
        """Initialize payment service patterns for email parsing."""
        return {
            PaymentSource.ZELLE: PaymentPattern(
                from_emails=frozenset(['noreply@zellepay.com', 'alert@zellepay.com']),
                subject_keywords=frozenset(['sent you', 'received', 'payment']),
                amount_pattern=r'\$([0-9,]+\.?[0-9]*)',
                name_pattern=r'([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+sent\s+you|from\s+([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)'
            ),
            PaymentSource.VENMO: PaymentPattern(
                from_emails=frozenset(['venmo@venmo.com', 'notifications@venmo.com']),
                subject_keywords=frozenset(['paid you', 'charged you', 'payment']),
                amount_pattern=r'\$([0-9,]+\.?[0-9]*)',
                name_pattern=r'([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+paid\s+you|from\s+([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)'
            ),
            PaymentSource.CASHAPP: PaymentPattern(
                from_emails=frozenset(['cash@square.com', 'support@cash.app']),
                subject_keywords=frozenset(['sent you', 'received', 'payment']),
                amount_pattern=r'\$([0-9,]+\.?[0-9]*)',
                name_pattern=r'([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+sent\s+you|from\s+([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)'
            ),
            PaymentSource.PAYPAL: PaymentPattern(
                from_emails=frozenset(['service@paypal.com', 'paypal@e.paypal.com']),
                subject_keywords=frozenset(['sent you', 'received', 'payment']),
                amount_pattern=r'\$([0-9,]+\.?[0-9]*)',
                name_pattern=r'([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+sent\s+you|from\s+([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)'
            )
        }
    
    def identify_payment_source(self, from_email: str, subject: str) -> PaymentSource | None:
        """Identify payment source from email metadata.
        
        Args:
            from_email: Email sender address
            subject: Email subject line
            
        Returns:
            PaymentSource if identified, None otherwise
        """
        for source, pattern in self.patterns.items():
            if pattern.matches_sender(from_email) and pattern.matches_subject(subject):
                return source
        return None
    
    def extract_amount(self, text: str, pattern: str) -> Decimal:
        """Extract payment amount from text.
        
        Args:
            text: Text to search for amount
            pattern: Regex pattern for amount extraction
            
        Returns:
            Decimal amount
            
        Raises:
            PaymentProcessorError: If amount cannot be extracted or parsed
        """
        match = re.search(pattern, text)
        if not match:
            raise PaymentProcessorError("Could not extract payment amount from text")
        
        amount_str = match.group(1).replace(',', '')
        try:
            return Decimal(amount_str)
        except InvalidOperation as e:
            raise PaymentProcessorError(f"Invalid amount format: {amount_str}") from e
    
    def extract_client_name(self, text: str, pattern: str) -> str:
        """Extract client name from text.
        
        Args:
            text: Text to search for client name
            pattern: Regex pattern for name extraction
            
        Returns:
            Client name or 'Unknown' if not found
        """
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Get the first non-empty group
            for group in match.groups():
                if group and group.strip():
                    return group.strip()
        return "Unknown"
    
    def parse_email_date(self, date_header: str) -> datetime:
        """Parse email date header.
        
        Args:
            date_header: Email date header string
            
        Returns:
            Parsed datetime or current time if parsing fails
        """
        try:
            return email_utils.parsedate_to_datetime(date_header)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse email date '{date_header}': {e}")
            return datetime.now()
    
    def process_email(self, email_message: EmailMessage, body: str, subject: str) -> PaymentRecord | None:
        """Process email to extract payment information.
        
        Args:
            email_message: Email message object
            body: Email body text
            subject: Email subject line
            
        Returns:
            PaymentRecord if payment found, None otherwise
        """
        from_email = email_message.get("From", "")
        
        # Identify payment source
        source = self.identify_payment_source(from_email, subject)
        if not source:
            return None
        
        pattern = self.patterns[source]
        combined_text = f"{body} {subject}"
        
        try:
            # Extract payment details
            amount = self.extract_amount(combined_text, pattern.amount_pattern)
            client_name = self.extract_client_name(combined_text, pattern.name_pattern)
            
            # Parse email date
            date_header = email_message.get("Date", "")
            payment_date = self.parse_email_date(date_header)
            
            return PaymentRecord(
                date=payment_date,
                amount=amount,
                source=source,
                client_name=client_name,
                email_subject=subject,
                processed_at=datetime.now()
            )
            
        except PaymentProcessorError as e:
            logger.error(f"Failed to process {source.value} payment: {e}")
            return None
    
    def get_supported_senders(self) -> list[str]:
        """Get list of all supported email senders.
        
        Returns:
            List of email addresses to monitor
        """
        senders = []
        for pattern in self.patterns.values():
            senders.extend(pattern.from_emails)
        return sorted(senders)
