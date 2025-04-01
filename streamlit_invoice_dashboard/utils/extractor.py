import sys
import os

# Add smart_bill_bot to sys.path
current_dir = os.path.dirname(__file__)
smart_bot_path = os.path.abspath(os.path.join(current_dir, '..', '..', 'smart_bill_bot'))
sys.path.insert(0, smart_bot_path)

from app.extractor import extract_fields

def extract_invoice_data(pdf_path):
    return extract_fields(pdf_path)
