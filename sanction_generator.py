# sanction_generator.py
import os
from datetime import datetime
from fpdf import FPDF

SANCTION_DIR = "sanctions"
os.makedirs(SANCTION_DIR, exist_ok=True)

def generate_sanction_pdf(customer, kyc_info, loan_amount, tenure_months, emi):
    """Create a simple, safe PDF sanction letter. Returns full file path."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "TATA CAPITAL - LOAN SANCTION LETTER", ln=True, align="C")
    pdf.ln(6)

    # Body
    pdf.set_font("Arial", size=11)
    now = datetime.now().strftime("%d-%m-%Y")
    pdf.multi_cell(0, 7, f"Date: {now}")
    pdf.ln(3)

    # Customer & KYC
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "Customer Details:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, f"Name: {customer.get('name')}")
    pdf.multi_cell(0, 7, f"Customer ID: {customer.get('cid')}")
    pdf.multi_cell(0, 7, f"PAN / Aadhaar (provided): {kyc_info.get('id_number')}")
    pdf.multi_cell(0, 7, f"Date of Birth: {kyc_info.get('dob')}")
    pdf.multi_cell(0, 7, f"Monthly Income (provided): INR {kyc_info.get('income')}")
    pdf.multi_cell(0, 7, f"Employment Type: {kyc_info.get('employment')}")
    pdf.ln(5)

    # Loan details
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "Loan Details:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, f"Loan Amount Sanctioned: INR {float(loan_amount):,.2f}")
    pdf.multi_cell(0, 7, f"Tenure: {tenure_months} months")
    pdf.multi_cell(0, 7, f"Estimated Monthly EMI: INR {float(emi):,.2f}")
    pdf.ln(6)

    # Terms
    pdf.multi_cell(
        0, 7,
        "This is a provisional sanction letter subject to final verification of "
        "documents and bank terms & conditions. Processing fees, applicable taxes "
        "and final interest rates will be shown in the formal sanction pack."
    )
    pdf.ln(8)
    pdf.multi_cell(0, 7, "Thank you for choosing Tata Capital.")
    pdf.ln(6)
    pdf.multi_cell(0, 7, "For any queries, contact our support team.")

    safe_cid = str(customer.get("cid"))
    file_name = f"sanction_{safe_cid}_{int(datetime.now().timestamp())}.pdf"
    full_path = os.path.join(SANCTION_DIR, file_name)

    pdf.output(full_path)
    return full_path
