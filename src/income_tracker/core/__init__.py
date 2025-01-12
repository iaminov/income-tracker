"""Core components for income tracking."""

from .email_client import EmailClient, EmailConnectionError
from .payment_processor import PaymentProcessor, PaymentProcessorError
from .tracker import IncomeTracker, IncomeTrackerError

__all__ = [
    "EmailClient",
    "EmailConnectionError",
    "PaymentProcessor", 
    "PaymentProcessorError",
    "IncomeTracker",
    "IncomeTrackerError",
]
