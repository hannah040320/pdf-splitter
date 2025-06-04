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

    # Define known supplier keywords (lowercase)
    supplier_keywords = {
        "ksi": "KSI Trading Corp",
        "regionmax": "Regionmax Co., Ltd.",
        "tyc": "TYC Americas"
    }

    # Step 1: Detect and group pages by supplier
    supplier_pages = {}

    for i in range(len(doc)):
        text = doc[i].get_text().lower()
        matched = False
        for keyword, supplier in supplier_keywords.items():
            if keyword in text:
                supplier_pages.setdefault(supplier, []).append(i)
                matched = True
                break
        if not matched:
            supplier_pages.setdefault("Unknown Supplier", []).append(i)

    # Step 2: Display download for each supplier PDF + offer PO split
    for supplier, pages in supplier_pages.items():
        st.markdown(f"### 📁 {supplier} ({len(pages)} page{'s' if len(pages) > 1 else ''})")
        supplier_doc = fitz.open()
        for page_num in pages:
            supplier_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        supplier_pdf_bytes = io.BytesIO()
        supplier_doc.save(supplier_pdf_bytes)
        st.download_button(f"⬇️ Download {supplier}", supplier_pdf_bytes.getvalue(), file_name=f"{supplier}.pdf")

        # Step 3: Optional PO Split
        if st.button(f"🔍 Split {supplier} by PO", key=supplier):
            st.info(f"Splitting {supplier} by PO...")
            po_map = {}
            po_text_preview = {}
            for page_num in range(len(supplier_doc)):
                text = supplier_doc[page_num].get_text()
                matches = re.findall(r"CL\d{6,}-NJ-\d+", text)
                po = matches[0] if matches else f"Page_{page_num+1}"
                po_map.setdefault(po, []).append(page_num)
                po_text_preview.setdefault(po, []).append(text[:500])

            for po, po_pages in po_map.items():
                po_doc = fitz.open()
                for p in po_pages:
                    po_doc.insert_pdf(supplier_doc, from_page=p, to_page=p)
                po_pdf_bytes = io.BytesIO()
                po_doc.save(po_pdf_bytes)
                st.markdown(f"**📄 {po} (Pages {', '.join(str(p+1) for p in po_pages)})**")
                st.download_button(f"⬇️ Download {po}.pdf", po_pdf_bytes.getvalue(), file_name=f"{po}.pdf")
                st.code("\n---\n".join(po_text_preview[po]), language='text')
