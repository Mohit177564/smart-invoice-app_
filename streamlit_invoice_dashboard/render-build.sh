#!/usr/bin/env bash

# System-level packages for OCR & PDF
apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libglib2.0-0 \
    libgl1-mesa-glx

# Then start Streamlit
streamlit run streamlit_invoice_dashboard/streamlit_app.py --server.port $PORT --server.enableCORS false
