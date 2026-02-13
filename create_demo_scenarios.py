"""
Generate comprehensive demo documents for all test scenarios.
Creates both auto-fixable (.docx) and manual-action (.pdf) files.

Run: python create_demo_scenarios.py
Output: demo_docs/
"""
import os
from pathlib import Path
from docx import Document
from docx.shared import Pt

# Directories
BASE_DIR = Path("demo_docs")
BASE_DIR.mkdir(parents=True, exist_ok=True)

def _add_para(doc, text, bold=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(11)
    return p

def _create_dummy_pdf(path):
    """Create a minimal valid PDF file."""
    content = (
        "%PDF-1.1\n"
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        "4 0 obj\n<< /Length 55 >>\nstream\n"
        "BT /F1 24 Tf 100 700 Td (This is a PDF file for Manual Action demo) Tj ET\n"
        "endstream\nendobj\n"
        "xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000213 00000 n \n"
        "trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n318\n%%EOF"
    )
    with open(path, "wb") as f:
        f.write(content.encode('latin-1'))
    print(f"[OK] {path} (Valid PDF)")

# ============================================================================
# SCENARIO 1: Operations Manual (Text + Visual Fix)
# ============================================================================
def create_ops_manual_v2():
    doc = Document()
    doc.add_heading("Operations Manual v2.1", level=0)
    _add_para(doc, "Last Updated: 2024-06-01")
    doc.add_paragraph()
    
    doc.add_heading("1. Accessing Settings", level=1)
    _add_para(doc, "Click the Gear icon (⚙) in the top-right header to open Settings.")
    _add_para(doc, "(Issue: New UI uses a side menu instead of top-right gear icon)")
    
    doc.add_heading("2. Login Screen", level=1)
    _add_para(doc, "[Image: Login_Screen_v2.png]")
    _add_para(doc, "Enter your ID and password on the blue login screen.")
    _add_para(doc, "(Visual Issue: Current login screen is white/minimalist design)")

    path = BASE_DIR / "Operations_Manual_v2.1.docx"
    doc.save(str(path))
    print(f"[OK] {path}")

# ============================================================================
# SCENARIO 2: New Hire Guide (Terminology Fix)
# ============================================================================
def create_new_hire_guide():
    doc = Document()
    doc.add_heading("New Hire Guide 2024", level=0)
    doc.add_paragraph()
    
    doc.add_heading("Getting Started", level=1)
    _add_para(doc, "1. Log in to the corporate portal.")
    _add_para(doc, "2. Check your Dashboard for daily tasks.")
    _add_para(doc, "(Issue: 'Dashboard' has been renamed to 'Home Screen')")
    
    path = BASE_DIR / "New_Hire_Guide_2024.docx"
    doc.save(str(path))
    print(f"[OK] {path}")

# ============================================================================
# SCENARIO 3: PDF (Manual Action)
# ============================================================================
def create_legacy_pdf():
    path = BASE_DIR / "Legacy_Product_Spec.pdf"
    _create_dummy_pdf(path)

# ============================================================================
# TRUTH SOURCES (Context)
# ============================================================================
def create_truth_docs():
    # 1. UI Update Spec
    doc = Document()
    doc.add_heading("UI Update Specification v3.0", level=0)
    _add_para(doc, "1. Settings moved to Side Menu.")
    _add_para(doc, "2. Login screen redesigned (White theme).")
    doc.save(str(BASE_DIR / "UI_Specs_v3.docx"))
    
    # 2. Terminology Guide
    doc2 = Document()
    doc2.add_heading("Terminology Guide 2025", level=0)
    _add_para(doc2, "'Dashboard' is deprecated. Use 'Home Screen'.")
    doc2.save(str(BASE_DIR / "Terminology_2025.docx"))
    print(f"[OK] Source docs created")

if __name__ == "__main__":
    print("\n>> Generating Demo Scenarios...\n")
    create_ops_manual_v2()
    create_new_hire_guide()
    create_legacy_pdf()
    create_truth_docs()
    print("\n>> Done!")
