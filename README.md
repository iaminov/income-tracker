# Payment Tracker for Tutoring Business

This Python script automatically monitors your email for payment notifications from Zelle, Venmo, CashApp, and PayPal, then updates an Excel spreadsheet with the payment details for income tracking.

## Files Created

- `payment_tracker.py` - Main payment tracking logic
- `config.py` - Configuration file (update with your email credentials)
- `run_payment_tracker.py` - Easy-to-use runner script
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Setup Instructions

### 1. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure Gmail Access

1. Go to your Google Account settings
2. Select Security
3. Turn on 2-Step Verification if not already enabled
4. Go to App passwords
5. Generate an app password for "Mail"
6. Copy the 16-character password (not your regular Gmail password)

### 3. Update Configuration

Edit `config.py` and update:
- `EMAIL_ADDRESS` - Your Gmail address
- `EMAIL_PASSWORD` - The app password from step 2
- `EXCEL_FILE_PATH` - Where to save the Excel file (default: "tutoring_income.xlsx")

## Usage

### Run the Payment Tracker

```powershell
python run_payment_tracker.py
```

The script will:
- Create an Excel file if it doesn't exist
- Monitor your email every 5 minutes (configurable)
- Extract payment information from emails
- Add new payments to the Excel spreadsheet
- Continue running until you stop it (Ctrl+C)

### Excel Output

The Excel file will contain these columns:
- **Date** - When the payment was received
- **Amount** - Payment amount
- **Source** - Payment service (Zelle, Venmo, CashApp, PayPal)
- **Client Name** - Extracted from the email
- **Email Subject** - Original email subject
- **Processed Date** - When the script processed the email

## Monitored Payment Services

- **Zelle** - noreply@zellepay.com, alert@zellepay.com
- **Venmo** - venmo@venmo.com, notifications@venmo.com
- **CashApp** - cash@square.com, support@cash.app
- **PayPal** - service@paypal.com, paypal@e.paypal.com

## Troubleshooting

- **"Authentication failed"** - Check your email address and app password
- **"No payments detected"** - Make sure you have payment emails in your inbox
- **Excel file issues** - Check file permissions and path

## Security Notes

- Never share your app password
- Use Gmail app passwords (not your regular password)
- The script only reads emails, it doesn't send or delete anything
- Your credentials are only stored locally in config.py

## Customization

You can modify the payment patterns in `payment_tracker.py` to:
- Add more payment services
- Adjust email pattern matching
- Change client name extraction logic
- Modify Excel output format
