#!/usr/bin/env bash

# Install system dependencies
apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libglib2.0-0 \
    libgl1-mesa-glx

# Run your Streamlit app
streamlit run streamlit_invoice_dashboard/streamlit_app.py --server.port $PORT --server.enableCORS false
