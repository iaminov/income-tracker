"""Main income tracker orchestrator that coordinates all components."""

import logging
import time
from contextlib import contextmanager
from typing import Generator

from .email_client import EmailClient, EmailConnectionError
from .payment_processor import PaymentProcessor
from ..storage import ExcelStorageHandler, StorageError
from ..models import PaymentRecord

logger = logging.getLogger(__name__)


class IncomeTrackerError(Exception):
    """Base exception for income tracker errors."""


class IncomeTracker:
    """Main income tracker that orchestrates email monitoring and payment processing."""
    
    def __init__(
        self,
        email_address: str,
        email_password: str,
        excel_file_path: str,
        check_interval: int = 300
    ) -> None:
        """Initialize income tracker.
        
        Args:
            email_address: Email address for IMAP connection
            email_password: App password for email account
            excel_file_path: Path to Excel file for storing records
            check_interval: Interval between email checks in seconds
        """
        self.email_client = EmailClient(email_address, email_password)
        self.payment_processor = PaymentProcessor()
        self.storage_handler = ExcelStorageHandler(excel_file_path)
        self.check_interval = check_interval
        self.processed_emails: set[str] = set()
        
        logger.info(f"Income tracker initialized with {len(self.payment_processor.get_supported_senders())} payment sources")
    
    def process_new_emails(self) -> int:
        """Process new emails and extract payment records.
        
        Returns:
            Number of new payment records processed
        """
        records_processed = 0
        supported_senders = self.payment_processor.get_supported_senders()
        
        for sender in supported_senders:
            try:
                email_ids = self.email_client.search_emails(sender)
                logger.debug(f"Found {len(email_ids)} emails from {sender}")
                
                for email_id in email_ids:
                    email_id_str = email_id.decode()
                    
                    # Skip already processed emails
                    if email_id_str in self.processed_emails:
                        continue
                    
                    # Fetch and process email
                    email_message = self.email_client.fetch_email(email_id)
                    if not email_message:
                        continue
                    
                    # Extract email content
                    subject = self.email_client.decode_subject(email_message)
                    body = self.email_client.extract_body(email_message)
                    
                    # Process for payment information
                    payment_record = self.payment_processor.process_email(
                        email_message, body, subject
                    )
                    
                    if payment_record:
                        try:
                            self.storage_handler.save_record(payment_record)
                            records_processed += 1
                            logger.info(
                                f"New payment: ${payment_record.amount} from "
                                f"{payment_record.client_name} via {payment_record.source.value}"
                            )
                        except StorageError as e:
                            logger.error(f"Failed to save payment record: {e}")
                    
                    # Mark as processed
                    self.processed_emails.add(email_id_str)
                    
            except EmailConnectionError as e:
                logger.error(f"Email connection error while processing {sender}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error processing emails from {sender}: {e}")
        
        return records_processed
    
    def run_single_check(self) -> dict[str, int]:
        """Run a single email check cycle.
        
        Returns:
            Dictionary with check results
        """
        logger.info("Starting email check cycle")
        start_time = time.time()
        
        try:
            records_processed = self.process_new_emails()
            duration = time.time() - start_time
            
            result = {
                "records_processed": records_processed,
                "duration_seconds": round(duration, 2),
                "total_emails_processed": len(self.processed_emails)
            }
            
            logger.info(
                f"Check cycle completed: {records_processed} new records, "
                f"{duration:.2f}s duration"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during email check cycle: {e}")
            return {
                "records_processed": 0,
                "duration_seconds": round(time.time() - start_time, 2),
                "error": str(e)
            }
    
    @contextmanager
    def monitoring_session(self) -> Generator[None, None, None]:
        """Context manager for monitoring session with proper cleanup."""
        logger.info("Starting income tracking monitoring session")
        try:
            yield
        except KeyboardInterrupt:
            logger.info("Monitoring session interrupted by user")
        except Exception as e:
            logger.error(f"Monitoring session error: {e}")
            raise
        finally:
            logger.info("Monitoring session ended")
    
    def run_continuous_monitoring(self) -> None:
        """Run continuous email monitoring.
        
        Monitors emails at specified intervals until interrupted.
        """
        logger.info(f"Starting continuous monitoring (check every {self.check_interval}s)")
        
        with self.monitoring_session():
            while True:
                try:
                    result = self.run_single_check()
                    
                    if "error" in result:
                        logger.warning("Check cycle had errors, continuing monitoring")
                    
                    logger.info(f"Next check in {self.check_interval} seconds")
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    logger.info("Continuous monitoring stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in monitoring loop: {e}")
                    logger.info("Retrying in 60 seconds...")
                    time.sleep(60)
    
    def get_statistics(self) -> dict:
        """Get comprehensive statistics about tracked payments.
        
        Returns:
            Dictionary with tracking statistics
        """
        try:
            storage_stats = self.storage_handler.get_summary_stats()
            
            return {
                "storage": storage_stats,
                "monitoring": {
                    "emails_processed": len(self.processed_emails),
                    "supported_payment_sources": len(self.payment_processor.patterns),
                    "supported_senders": self.payment_processor.get_supported_senders(),
                    "check_interval_seconds": self.check_interval
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}
    
    def validate_configuration(self) -> dict[str, bool]:
        """Validate tracker configuration.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {}
        
        # Test email connection
        try:
            with self.email_client.connection():
                validation_results["email_connection"] = True
                logger.info("Email connection validation: PASSED")
        except Exception as e:
            validation_results["email_connection"] = False
            logger.error(f"Email connection validation: FAILED - {e}")
        
        # Test storage access
        try:
            self.storage_handler._ensure_file_exists()
            validation_results["storage_access"] = True
            logger.info("Storage access validation: PASSED")
        except Exception as e:
            validation_results["storage_access"] = False
            logger.error(f"Storage access validation: FAILED - {e}")
        
        # Test payment processor
        try:
            supported_senders = self.payment_processor.get_supported_senders()
            validation_results["payment_processor"] = len(supported_senders) > 0
            logger.info(f"Payment processor validation: PASSED ({len(supported_senders)} senders)")
        except Exception as e:
            validation_results["payment_processor"] = False
            logger.error(f"Payment processor validation: FAILED - {e}")
        
        return validation_results
