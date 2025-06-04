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
    st.success("File uploaded. Splitting by supplier...")
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    # Define PO-to-supplier mapping explicitly
    po_supplier_lookup = {
        "CL250604D-NJ-2": "Maxzone",
        "CL250602G-NJ-2": "TYC",
        "CL250602E-NJ-2": "Eagle",
        "CL250602K-NJ-2": "KSI"
    }

    # Step 1: Detect and group pages by PO number and supplier
    supplier_po_pages = {}

    for i in range(len(doc)):
        text = doc[i].get_text()
        matches = re.findall(r"CL\d{6,}-NJ-\d+", text)
        if matches:
            po = matches[0]
            supplier = po_supplier_lookup.get(po, "Unknown Supplier")
            supplier_po_pages.setdefault(supplier, {}).setdefault(po, []).append(i)
        else:
            supplier_po_pages.setdefault("Unknown Supplier", {}).setdefault("Unmatched", []).append(i)

    # Step 2: Display download buttons grouped by supplier and PO
    for supplier, po_dict in supplier_po_pages.items():
        st.markdown(f"### 📁 {supplier}")
        for po, po_pages in po_dict.items():
            po_doc = fitz.open()
            for page_num in po_pages:
                po_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            po_pdf_bytes = io.BytesIO()
            po_doc.save(po_pdf_bytes)
            st.markdown(f"**📄 {po} (Pages {', '.join(str(p+1) for p in po_pages)})**")
            st.download_button(f"⬇️ Download {po}.pdf", po_pdf_bytes.getvalue(), file_name=f"{po}.pdf")
            preview_text = "\n---\n".join([doc[p].get_text()[:500] for p in po_pages])
            st.code(preview_text, language='text')
