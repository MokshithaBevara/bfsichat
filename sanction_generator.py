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
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "TATA CAPITAL - LOAN SANCTION LETTER", ln=True, align="C")
    pdf.ln(8)

    # Date
    pdf.set_font("Arial", size=11)
    now = datetime.now().strftime("%d-%m-%Y")
    pdf.cell(0, 8, f"Date: {now}", ln=True)
    pdf.ln(5)

    # Customer Details
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "CUSTOMER DETAILS:", ln=True)
    pdf.set_font("Arial", size=11)
    
    pdf.cell(140, 7, f"Name: {customer.get('name', 'N/A')}", ln=True)
    pdf.cell(140, 7, f"Customer ID: {customer.get('cid', 'N/A')}", ln=True)
    pdf.cell(140, 7, f"PAN/Aadhaar: {str(kyc_info.get('id_number', 'N/A'))[:20]}", ln=True)
    pdf.cell(140, 7, f"DOB: {kyc_info.get('dob', 'N/A')}", ln=True)
    pdf.cell(140, 7, f"Income: INR {kyc_info.get('income', 0):,.0f}", ln=True)
    pdf.cell(140, 7, f"Employment: {kyc_info.get('employment', 'N/A')}", ln=True)
    pdf.ln(8)

    # Loan Details
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "LOAN DETAILS:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(140, 7, f"Amount: INR {float(loan_amount):,.0f}", ln=True)
    pdf.cell(140, 7, f"Tenure: {tenure_months} months", ln=True)
    pdf.cell(140, 7, f"EMI: INR {float(emi):,.0f}", ln=True)
    pdf.ln(10)

    # Terms
    pdf.set_font("Arial", size=10)
    terms = [
        "This is a provisional sanction letter subject to final verification.",
        "Processing fees, taxes and final interest rates apply.",
        "Formal sanction pack will be provided post-document verification."
    ]
    for term in terms:
        pdf.cell(0, 7, term, ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Thank you for choosing Tata Capital.", ln=True, align="C")
    pdf.cell(0, 8, "For queries, contact our support team.", ln=True, align="C")

    # Safe filename
    safe_cid = str(customer.get("cid", "unknown"))[:10]
    file_name = f"sanction_{safe_cid}_{int(datetime.now().timestamp())}.pdf"
    full_path = os.path.join(SANCTION_DIR, file_name)

    pdf.output(full_path)
    return full_path
