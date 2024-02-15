"""Income Tracker - A sophisticated payment monitoring and tracking system."""

__version__ = "1.0.0"
__author__ = "Income Tracker Team"
__description__ = "Advanced income tracking system for freelancers and small businesses"

from .core.tracker import IncomeTracker
from .core.email_client import EmailClient
from .core.payment_processor import PaymentProcessor

__all__ = [
    "IncomeTracker",
    "EmailClient", 
    "PaymentProcessor",
]
