"""Configuration module for income tracker."""
import os
from pathlib import Path

# Email Configuration
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Excel File Configuration
EXCEL_FILE_PATH = os.getenv("EXCEL_FILE_PATH", "tutoring_income.xlsx")

# Monitoring Configuration
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))
