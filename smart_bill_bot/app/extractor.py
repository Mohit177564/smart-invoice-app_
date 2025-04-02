import os
import pytesseract
import pdf2image
from PIL import Image
import re
from datetime import datetime
import cv2

def extract_text_from_pdf(pdf_path):
    images = pdf2image.convert_from_path(pdf_path)
    text = "\n".join([pytesseract.image_to_string(img) for img in images])
    return text.strip()

def extract_text_from_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    processed_image_path = "processed.png"
    cv2.imwrite(processed_image_path, thresh)
    text = pytesseract.image_to_string(Image.open(processed_image_path))
    return text.strip()

def extract_invoice_details(text):
    extracted_data = {
        "vendor": "Unknown",
        "vendor_address": "Unknown",
        "invoice_number": "Unknown",
        "date": "Unknown",
        "amount": "Unknown"
    }

    lines = text.strip().splitlines()

    # ✅ 1. Try extracting from www.vendor.com
    vendor_match = re.search(r"www\.(\w+)\.com", text, re.IGNORECASE)
    if vendor_match:
        extracted_data["vendor"] = vendor_match.group(1).capitalize()

    # ✅ 2. Extract from "Remit To:" block
    elif remit_block := re.search(r"Remit To:\s*([\s\S]*?)(?=\nPh\.|\nFax|\nEmail|\nWebsite|\n)", text, re.IGNORECASE):
        remit_lines = remit_block.group(1).strip().splitlines()
        if remit_lines:
            extracted_data["vendor"] = remit_lines[0].strip()
            extracted_data["vendor_address"] = remit_block.group(1).strip().replace("\n", " ")

    # ✅ 3. Legal suffix match: P.C., LLC, Inc, Corp
    elif legal_match := re.search(r"(?i)([A-Z][A-Z\s&]+(P\.?C\.?|LLC|INC|CORP))", text):
        extracted_data["vendor"] = legal_match.group(1).title()

    # ✅ 4. Fallback: top uppercase lines (exclude "ATTORNEYS AT LAW" etc.)
    if extracted_data["vendor"] == "Unknown":
        for line in lines[:10]:
            if (
                line.strip().isupper()
                and len(line.strip().split()) <= 6
                and "ATTORNEY" not in line.upper()
                and not re.search(r"\d", line)
            ):
                extracted_data["vendor"] = line.strip().title()
                break

    # ✅ Date detection
    date_patterns = [
        r"(?:Invoice Date|Date Issued|Date)[\s:]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})",
        r"(?:Invoice Date|Date Issued|Date)[\s:]*([A-Za-z]+ \d{1,2}, \d{4})"
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(1).strip()
            try:
                extracted_data["date"] = datetime.strptime(date_str, "%B %d, %Y").strftime("%m/%d/%Y")
            except ValueError:
                extracted_data["date"] = date_str

    # ✅ Invoice Number
    invoice_match = re.search(r"(?:Invoice\s*(#|No\.?|Number)?[\s:]*)\s*(\d{4,})", text, re.IGNORECASE)
    if invoice_match:
        extracted_data["invoice_number"] = invoice_match.group(2).strip()

    # ✅ Amount Detection
    amount_order = [
        r"Balance Due[\s:]*\$?([\d,]+\.\d{2})",
        r"Total Due[\s:]*\$?([\d,]+\.\d{2})",
        r"Amount Due[\s:]*\$?([\d,]+\.\d{2})",
        r"Total[\s:]*\$?([\d,]+\.\d{2})",
        r"Grand Total[\s:]*\$?([\d,]+\.\d{2})"
    ]
    for pattern in amount_order:
        amount_match = re.search(pattern, text, re.IGNORECASE)
        if amount_match:
            extracted_data["amount"] = amount_match.group(1).strip()
            break

    return extracted_data

def extract_fields(file_path):
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_image(file_path)

    extracted_data = extract_invoice_details(text)
    return extracted_data
