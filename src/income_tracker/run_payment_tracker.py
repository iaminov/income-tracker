#!/usr/bin/env python3
"""
Payment Tracker Runner Script
This script runs the payment tracker using settings from config.py
"""

from payment_tracker import PaymentTracker
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, EXCEL_FILE_PATH, CHECK_INTERVAL
import sys

def main():
    print("Payment Tracker for Tutoring Business")
    print("=====================================")
    
    # Check if configuration has been updated
    if EMAIL_ADDRESS == "your_email@gmail.com" or EMAIL_PASSWORD == "your_app_password":
        print("❌ CONFIGURATION REQUIRED!")
        print("\nPlease update the following files with your information:")
        print("1. config.py - Update EMAIL_ADDRESS and EMAIL_PASSWORD")
        print("\nSetup Instructions:")
        print("• EMAIL_ADDRESS: Your Gmail address")
        print("• EMAIL_PASSWORD: Your Gmail App Password (not your regular password)")
        print("\nGmail App Password Setup:")
        print("1. Go to your Google Account settings")
        print("2. Select Security")
        print("3. Turn on 2-Step Verification if not already enabled")
        print("4. Go to App passwords")
        print("5. Generate an app password for 'Mail'")
        print("6. Use that 16-character password in config.py")
        print("\nAfter updating config.py, run this script again.")
        return
    
    print("✅ Configuration looks good!")
    print(f"📧 Email: {EMAIL_ADDRESS}")
    print(f"📊 Excel file: {EXCEL_FILE_PATH}")
    print(f"⏰ Check interval: {CHECK_INTERVAL} seconds")
    print("\nPayment services monitored: Zelle, Venmo, CashApp, PayPal")
    print("\nStarting payment monitoring...")
    print("Press Ctrl+C to stop")
    
    try:
        # Create and run the payment tracker
        tracker = PaymentTracker(EMAIL_ADDRESS, EMAIL_PASSWORD, EXCEL_FILE_PATH)
        tracker.run_continuous_monitoring(check_interval=CHECK_INTERVAL)
        
    except KeyboardInterrupt:
        print("\n\n✅ Payment tracker stopped by user")
    except Exception as e:
        print(f"\n❌ Error running payment tracker: {e}")
        print("Make sure your email credentials are correct and you have an internet connection.")

if __name__ == "__main__":
    main()
