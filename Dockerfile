# Use official Python image
FROM python:3.11-slim

# System dependencies for OCR & PDF rendering
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy everything
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Run Streamlit app
CMD ["streamlit", "run", "streamlit_invoice_dashboard/streamlit_app.py", "--server.port=8080", "--server.enableCORS=false"]
