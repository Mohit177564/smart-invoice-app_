import os
import pytesseract
import pdf2image
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image
import re
from datetime import datetime
import cv2

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

saved_invoices = []

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

    # ✅ Vendor from top few lines
    for line in lines[:6]:
        if line.strip() and line.strip().isupper() and len(line.strip().split()) <= 6:
            extracted_data["vendor"] = line.strip().title()
            break

    # ✅ Vendor Address (Remit To)
    remit_to_match = re.search(r"Remit To:\s*([\s\S]*?)(?=\nPh\.|\nFax|\nEmail|\nWebsite)", text, re.IGNORECASE)
    if remit_to_match:
        extracted_data["vendor_address"] = remit_to_match.group(1).strip().replace("\n", " ")

    # ✅ Date (Invoice Date or Table)
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

    # ✅ Invoice Number (Label)
    invoice_match = re.search(r"(?:Invoice\s*(#|No\.?|Number)?[\s:]*)\s*(\d{4,})", text, re.IGNORECASE)
    if invoice_match:
        extracted_data["invoice_number"] = invoice_match.group(2).strip()

    # ✅ Amount (prioritize Balance Due > Total Due > Total)
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

    # ✅ Table fallback (one-liner for INVOICE # DATE TOTAL DUE ...)
    table_row_match = re.search(
        r"INVOICE\s*#\s+DATE\s+TOTAL\s+DUE[\s\S]{0,50}?(\d{4,})\s+(\d{1,2}/\d{1,2}/\d{4})\s+\$?([\d,]+\.\d{2})",
        text,
        re.IGNORECASE
    )
    if table_row_match:
        if extracted_data["invoice_number"] == "Unknown":
            extracted_data["invoice_number"] = table_row_match.group(1).strip()
        if extracted_data["date"] == "Unknown":
            extracted_data["date"] = table_row_match.group(2).strip()
        if extracted_data["amount"] == "Unknown":
            extracted_data["amount"] = table_row_match.group(3).strip()

    return extracted_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract_invoice_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    if file.filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_image(file_path)

    print("\n📝 OCR Extracted Text:\n", text)

    extracted_data = extract_invoice_details(text)
    extracted_data["text"] = text

    return jsonify(extracted_data)

@app.route('/save', methods=['POST'])
def save_invoice():
    global saved_invoices
    data = request.json
    saved_invoices.append(data)
    return jsonify({"message": "Invoice saved!", "data": saved_invoices})

@app.route('/get_saved', methods=['GET'])
def get_saved_invoices():
    return jsonify(saved_invoices)

@app.route('/delete', methods=['POST'])
def delete_invoice():
    global saved_invoices
    invoice_number = request.json.get("invoice_number")
    saved_invoices = [inv for inv in saved_invoices if inv["invoice_number"] != invoice_number]
    return jsonify({"message": "Invoice deleted!", "data": saved_invoices})

@app.route('/download', methods=['GET'])
def download_excel():
    df = pd.DataFrame(saved_invoices)
    excel_path = "invoices.xlsx"
    df.to_excel(excel_path, index=False)
    return send_file(excel_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
