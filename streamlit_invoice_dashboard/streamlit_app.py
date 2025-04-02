import streamlit as st
import pandas as pd
import os
import fitz  # PyMuPDF
from PIL import Image
import tempfile
from utils.extractor import extract_invoice_data
from io import BytesIO

def export_excel_file(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, index=False)
    output.seek(0)
    return output.getvalue()

st.set_page_config(page_title="Smart Invoice Extractor", layout="wide")
st.markdown("<h1 style='text-align: center;'>📄 Smart Invoice Extractor Dashboard</h1>", unsafe_allow_html=True)

if "invoice_queue" not in st.session_state:
    st.session_state.invoice_queue = []

if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = {}

st.sidebar.header("📂 Upload Invoices")
uploaded_files = st.sidebar.file_uploader(
    "Upload PDFs or Images", 
    type=["pdf", "jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if st.sidebar.button("💾 Save Queue"):
    df = pd.DataFrame(st.session_state.invoice_queue)
    df.to_csv("saved_queue.csv", index=False)
    st.sidebar.success("Queue saved to saved_queue.csv")

if st.sidebar.button("📂 Load Queue"):
    if os.path.exists("saved_queue.csv"):
        try:
            df = pd.read_csv("saved_queue.csv")
            st.session_state.invoice_queue = df.to_dict(orient="records")
            st.sidebar.success("Queue loaded!")
        except pd.errors.EmptyDataError:
            st.session_state.invoice_queue = []
            st.sidebar.warning("Saved queue is empty.")
    else:
        st.sidebar.error("No saved queue found!")

if uploaded_files and st.sidebar.button("🧠 Process All to Queue"):
    for file in uploaded_files:
        ext = os.path.splitext(file.name)[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_file.write(file.read())
            temp_path = temp_file.name

        try:
            extracted = extract_invoice_data(temp_path)
            if extracted:
                st.session_state.invoice_queue.append(extracted)
        except Exception as e:
            st.warning(f"Failed to process {file.name}: {e}")
    st.sidebar.success("All files processed and added to queue.")

if uploaded_files:
    selected_file = st.selectbox("Choose a file to preview & extract", [f.name for f in uploaded_files])
    for file in uploaded_files:
        if file.name == selected_file:
            ext = os.path.splitext(file.name)[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                temp_file.write(file.read())
                temp_file_path = temp_file.name

            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("📑 Invoice Preview")
                doc = fitz.open(temp_file_path)
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                st.image(img, use_column_width=True)

            with col2:
                st.subheader("🧠 Extracted Data")
                if st.button("Extract Data"):
                    extracted = extract_invoice_data(temp_file_path)
                    st.session_state.extracted_data = extracted

                if st.session_state.extracted_data:
                    for k, v in st.session_state.extracted_data.items():
                        st.write(f"**{k}:** {v}")

                    if st.button("➕ Add to Queue"):
                        st.session_state.invoice_queue.append(st.session_state.extracted_data.copy())
                        st.success("Added to queue.")
                        st.session_state.extracted_data = {}

if st.session_state.invoice_queue:
    st.subheader("📝 Queued Invoices")
    df = pd.DataFrame(st.session_state.invoice_queue)

    remove_option = st.selectbox("Select invoice to remove", df["invoice_number"])
    if st.button("❌ Remove from Queue"):
        st.session_state.invoice_queue = [
            inv for inv in st.session_state.invoice_queue if inv["invoice_number"] != remove_option
        ]
        df_updated = pd.DataFrame(st.session_state.invoice_queue)
        df_updated.to_csv("saved_queue.csv", index=False)
        st.success(f"Removed invoice {remove_option} and updated saved queue.")

    st.dataframe(df)
    excel_data = export_excel_file(df)
    st.download_button("📥 Download All as Excel", data=excel_data, file_name="invoices.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
