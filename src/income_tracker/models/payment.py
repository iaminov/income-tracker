"""Payment data models for income tracking."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path


class PaymentSource(Enum):
    """Supported payment service providers."""
    ZELLE = "Zelle"
    VENMO = "Venmo"
    CASHAPP = "CashApp"
    PAYPAL = "PayPal"


@dataclass(frozen=True)
class PaymentRecord:
    """Immutable payment record data structure."""
    
    date: datetime
    amount: Decimal
    source: PaymentSource
    client_name: str
    email_subject: str
    processed_at: datetime
    
    def to_dict(self) -> dict[str, str | datetime | Decimal]:
        """Convert payment record to dictionary for Excel export."""
        return {
            "Date": self.date.strftime("%Y-%m-%d"),
            "Amount": self.amount,
            "Source": self.source.value,
            "Client Name": self.client_name,
            "Email Subject": self.email_subject,
            "Processed Date": self.processed_at.strftime("%Y-%m-%d %H:%M:%S")
        }


@dataclass(frozen=True)
class PaymentPattern:
    """Configuration for payment service email parsing."""
    
    from_emails: frozenset[str]
    subject_keywords: frozenset[str]
    amount_pattern: str
    name_pattern: str
    
    def matches_sender(self, from_email: str) -> bool:
        """Check if email sender matches this payment service."""
        return any(sender in from_email.lower() for sender in self.from_emails)
    
    def matches_subject(self, subject: str) -> bool:
        """Check if email subject contains payment keywords."""
        return any(keyword in subject.lower() for keyword in self.subject_keywords)
