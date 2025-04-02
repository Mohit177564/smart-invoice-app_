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

    # ✅ 1. Legal suffix or known law firm pattern
    firm_match = re.search(r"([A-Z][A-Za-z,&\s]+(?:LLP|LLC|P\.?C\.?|Inc\.?|Group))", text, re.IGNORECASE)
    if firm_match:
        extracted_data["vendor"] = firm_match.group(1).strip()

    # ✅ 2. Remit To fallback
    elif remit_block := re.search(r"Remit To:\s*([\s\S]*?)(?=\nPh\.|\nFax|\nEmail|\nWebsite|\n)", text, re.IGNORECASE):
        remit_lines = remit_block.group(1).strip().splitlines()
        if remit_lines:
            extracted_data["vendor"] = remit_lines[0].strip()
            extracted_data["vendor_address"] = remit_block.group(1).strip().replace("\n", " ")

    # ✅ 3. Uppercase fallback
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

    # ✅ 4. Improved table row with pipe `|` support
    table_match = re.search(
        r"Matter\s*#.*?Invoice\s*#.*?Amount.*?\n\S+\s*[| ]\s*(\d{1,2}/\d{1,2}/\d{4})\s+(\d+)\s+\$?([\d,]+\.\d{2})",
        text,
        re.IGNORECASE | re.DOTALL
    )
    if table_match:
        extracted_data["date"] = table_match.group(1).strip()
        extracted_data["invoice_number"] = table_match.group(2).strip()
        extracted_data["amount"] = table_match.group(3).strip()

    # ✅ 5. Generic date fallback
    if extracted_data["date"] == "Unknown":
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
                break

    # ✅ 6. Invoice number fallback
    if extracted_data["invoice_number"] == "Unknown":
        invoice_match = re.search(r"(?:Invoice\s*(#|No\.?|Number)?[\s:]*)\s*(\d{4,})", text, re.IGNORECASE)
        if invoice_match:
            extracted_data["invoice_number"] = invoice_match.group(2).strip()

    # ✅ 7. Amount fallback
    if extracted_data["amount"] == "Unknown":
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
