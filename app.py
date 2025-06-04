import streamlit as st
import fitz  # PyMuPDF
import io
import zipfile
import os
import re

st.set_page_config(page_title="PDF Splitter by Supplier & PO", layout="wide")
st.title("📄 AI PDF Splitter: Supplier → PO")

uploaded_file = st.file_uploader("Upload a Pickup List PDF", type=["pdf"])

if uploaded_file:
    st.success("File uploaded. Processing...")
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    # Define known supplier keywords
    supplier_keywords = [
        "KSI Trading Corp", "Regionmax", "TYC Americas"
    ]

    # Step 1: Split by supplier
    supplier_pages = {}

    for i in range(len(doc)):
        text = doc[i].get_text()
        found = False
        for keyword in supplier_keywords:
            if keyword.lower() in text.lower():
                supplier_pages.setdefault(keyword, []).append(i)
                found = True
                break
        if not found:
            supplier_pages.setdefault("Unknown Supplier", []).append(i)

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for supplier, pages in supplier_pages.items():
            supplier_doc = fitz.open()
            for page_num in pages:
                supplier_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            # Step 2: Split each supplier doc by PO# (based on keyword, no OCR)
            po_map = {}
            for page_num in range(len(supplier_doc)):
                text = supplier_doc[page_num].get_text()
                matches = re.findall(r"CL\d{6,}-NJ-\d+", text)
                po = matches[0] if matches else f"Page_{page_num+1}"
                po_map.setdefault(po, []).append(page_num)

            for po, po_pages in po_map.items():
                po_doc = fitz.open()
                for p in po_pages:
                    po_doc.insert_pdf(supplier_doc, from_page=p, to_page=p)
                fname = f"{supplier}/{po}.pdf"
                filepath = os.path.join(output_dir, fname)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                po_doc.save(filepath)
                zipf.write(filepath, arcname=fname)

    st.success("Processing complete! Download your ZIP below.")
    st.download_button("Download ZIP", zip_buffer.getvalue(), file_name="split_picklist_by_supplier_PO.zip")
