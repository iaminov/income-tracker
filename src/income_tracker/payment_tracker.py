import imaplib
import email
import re
import pandas as pd
from datetime import datetime
import time
import os
from email.header import decode_header
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PaymentTracker:
    def __init__(self, email_address, email_password, excel_file_path):
        self.email_address = email_address
        self.email_password = email_password
        self.excel_file_path = excel_file_path
        self.processed_uids = set()
        
        # Payment service email patterns
        self.payment_patterns = {
            'Zelle': {
                'from_emails': ['noreply@zellepay.com', 'alert@zellepay.com'],
                'subject_keywords': ['sent you', 'received', 'payment'],
                'amount_pattern': r'\$([0-9,]+\.?[0-9]*)',
                'name_pattern': r'([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+sent\s+you|from\s+([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)'
            },
            'Venmo': {
                'from_emails': ['venmo@venmo.com', 'notifications@venmo.com'],
                'subject_keywords': ['paid you', 'charged you', 'payment'],
                'amount_pattern': r'\$([0-9,]+\.?[0-9]*)',
                'name_pattern': r'([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+paid\s+you|from\s+([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)'
            },
            'CashApp': {
                'from_emails': ['cash@square.com', 'support@cash.app'],
                'subject_keywords': ['sent you', 'received', 'payment'],
                'amount_pattern': r'\$([0-9,]+\.?[0-9]*)',
                'name_pattern': r'([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+sent\s+you|from\s+([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)'
            },
            'PayPal': {
                'from_emails': ['service@paypal.com', 'paypal@e.paypal.com'],
                'subject_keywords': ['sent you', 'received', 'payment'],
                'amount_pattern': r'\$([0-9,]+\.?[0-9]*)',
                'name_pattern': r'([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+sent\s+you|from\s+([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)'
            }
        }
        
        # Initialize Excel file if it doesn't exist
        self.initialize_excel_file()
    
    def initialize_excel_file(self):
        """Initialize Excel file with headers if it doesn't exist"""
        if not os.path.exists(self.excel_file_path):
            df = pd.DataFrame(columns=['Date', 'Amount', 'Source', 'Client Name', 'Email Subject', 'Processed Date'])
            df.to_excel(self.excel_file_path, index=False)
            logger.info(f"Created new Excel file: {self.excel_file_path}")
    
    def connect_to_email(self):
        """Connect to email server"""
        try:
            # Connect to Gmail IMAP server
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.email_address, self.email_password)
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to email: {e}")
            return None
    
    def extract_payment_info(self, email_body, subject, source):
        """Extract payment information from email content"""
        pattern_config = self.payment_patterns[source]
        
        # Extract amount
        amount_match = re.search(pattern_config['amount_pattern'], email_body + ' ' + subject)
        amount = amount_match.group(1) if amount_match else 'Unknown'
        
        # Extract client name
        name_match = re.search(pattern_config['name_pattern'], email_body + ' ' + subject, re.IGNORECASE)
        client_name = 'Unknown'
        if name_match:
            # Get the first non-empty group
            client_name = next((group for group in name_match.groups() if group), 'Unknown')
        
        return amount, client_name
    
    def process_email(self, mail_server, email_id):
        """Process a single email and extract payment information"""
        try:
            # Fetch the email
            status, msg_data = mail_server.fetch(email_id, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Get email details
            subject = decode_header(email_message["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            from_email = email_message.get("From", "")
            date_received = email_message.get("Date", "")
            
            # Parse date
            try:
                parsed_date = email.utils.parsedate_to_datetime(date_received)
                formatted_date = parsed_date.strftime('%Y-%m-%d')
            except:
                formatted_date = datetime.now().strftime('%Y-%m-%d')
            
            # Get email body
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()
            
            # Determine payment source
            source = None
            for payment_source, config in self.payment_patterns.items():
                if any(sender in from_email.lower() for sender in config['from_emails']):
                    if any(keyword in subject.lower() for keyword in config['subject_keywords']):
                        source = payment_source
                        break
            
            if source:
                amount, client_name = self.extract_payment_info(body, subject, source)
                
                # Add to Excel
                self.add_to_excel(formatted_date, amount, source, client_name, subject)
                logger.info(f"Processed {source} payment: ${amount} from {client_name}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing email {email_id}: {e}")
            return False
    
    def add_to_excel(self, date, amount, source, client_name, subject):
        """Add payment information to Excel file"""
        try:
            # Read existing data
            df = pd.read_excel(self.excel_file_path)
            
            # Create new row
            new_row = {
                'Date': date,
                'Amount': amount,
                'Source': source,
                'Client Name': client_name,
                'Email Subject': subject,
                'Processed Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add new row
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save to Excel
            df.to_excel(self.excel_file_path, index=False)
            logger.info(f"Added payment record to Excel: {source} - ${amount} - {client_name}")
            
        except Exception as e:
            logger.error(f"Error adding to Excel: {e}")
    
    def check_for_new_emails(self):
        """Check for new payment emails"""
        mail = self.connect_to_email()
        if not mail:
            return
        
        try:
            mail.select('inbox')
            
            # Search for emails from payment services
            all_senders = []
            for config in self.payment_patterns.values():
                all_senders.extend(config['from_emails'])
            
            for sender in all_senders:
                try:
                    status, messages = mail.search(None, f'(FROM "{sender}")')
                    email_ids = messages[0].split()
                    
                    for email_id in email_ids:
                        uid = email_id.decode()
                        if uid not in self.processed_uids:
                            if self.process_email(mail, email_id):
                                self.processed_uids.add(uid)
                                
                except Exception as e:
                    logger.error(f"Error searching emails from {sender}: {e}")
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
    
    def run_continuous_monitoring(self, check_interval=300):
        """Run continuous monitoring for new emails"""
        logger.info("Starting continuous email monitoring...")
        logger.info(f"Excel file: {self.excel_file_path}")
        logger.info(f"Check interval: {check_interval} seconds")
        
        while True:
            try:
                logger.info("Checking for new payment emails...")
                self.check_for_new_emails()
                logger.info(f"Waiting {check_interval} seconds before next check...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                logger.info("Retrying in 60 seconds...")
                time.sleep(60)

def main():
    # Configuration
    EMAIL_ADDRESS = "your_email@gmail.com"  # Replace with your email
    EMAIL_PASSWORD = "your_app_password"    # Replace with your app password
    EXCEL_FILE_PATH = "tutoring_income.xlsx"  # Excel file path
    
    print("Payment Tracker for Tutoring Business")
    print("=====================================")
    print("This script will monitor your email for payment notifications and update an Excel spreadsheet.")
    print("\nIMPORTANT SETUP REQUIRED:")
    print("1. Enable 2-factor authentication on your Gmail account")
    print("2. Generate an App Password for this script")
    print("3. Update the EMAIL_ADDRESS and EMAIL_PASSWORD variables in this script")
    print("4. Make sure the Excel file path is correct")
    print("\nPayment services monitored: Zelle, Venmo, CashApp, PayPal")
    print(f"Excel file will be created at: {EXCEL_FILE_PATH}")
    

    +-# Uncomment the lines below and update with your actual credentials
    # tracker = PaymentTracker(EMAIL_ADDRESS, EMAIL_PASSWORD, EXCEL_FILE_PATH)
    # tracker.run_continuous_monitoring(check_interval=300)  # Check every 5 minutes
    
    print("\nTo run the script:")
    print("1. Update the EMAIL_ADDRESS and EMAIL_PASSWORD variables")
    print("2. Uncomment the last two lines in the main() function")
    print("3. Run the script")

if __name__ == "__main__":
    main()
