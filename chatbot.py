import csv
import time
import os
import random
from datetime import datetime
from fpdf import FPDF

CUSTOMER_FILE = "customers.csv"
SANCTION_DIR = "sanctions"
os.makedirs(SANCTION_DIR, exist_ok=True)

# -------------------------
# CREATE CUSTOMER
# -------------------------
def create_customer(name, password, income, age, employment):
    cid = str(int(time.time()))[-6:]  # simple 6-digit ID
    credit_score = random.randint(650, 850)  # dummy credit score

    file_exists = os.path.isfile(CUSTOMER_FILE)
    with open(CUSTOMER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["customer_id", "name", "password", "monthly_income", "age",
                             "employment_type", "existing_emi", "credit_score"])
        writer.writerow([cid, name, password, income, age, employment, 0, credit_score])
    return cid


# -------------------------
# GET CUSTOMER BY CID
# -------------------------
def get_customer_by_cid(cid):
    try:
        with open(CUSTOMER_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["customer_id"] == cid:
                    return {
                        "cid": row["customer_id"],
                        "name": row["name"],
                        "password": row["password"],
                        "income": float(row["monthly_income"]),
                        "age": int(row["age"]),
                        "employment": row["employment_type"],
                        "credit_score": int(row["credit_score"]),
                        "existing_emi": float(row.get("existing_emi") or 0),
                    }
    except Exception:
        return None
    return None


# -------------------------
# MASTER AGENT
# -------------------------
class MasterAgent:
    def __init__(self, cid):
        self.cid = cid
        self.context = []

    def start_chat(self):
        return "Hello! I'm your Tata Capital Loan Assistant. I can check eligibility, process loans, and answer queries."

    def reply(self, msg):
        self.context.append(f"User: {msg}")
        customer = get_customer_by_cid(self.cid)

        # simple keyword-based responses
        msg_lower = msg.lower()
        if "eligibility" in msg_lower:
            return self.check_eligibility(customer)
        elif "loan" in msg_lower:
            return self.loan_request(customer, msg)
        else:
            return "I can help with checking eligibility or processing a loan. Try: 'Check eligibility' or 'Request loan 500000'."

    # -------------------------
    # CHECK ELIGIBILITY
    # -------------------------
    def check_eligibility(self, customer):
        pre_limit = customer["income"] * 12  # 12 months salary
        return f"Your credit score is {customer['credit_score']}. Pre-approved loan limit: INR {pre_limit:.2f}"

    # -------------------------
    # PROCESS LOAN REQUEST
    # -------------------------
    def loan_request(self, customer, msg):
        import re
        nums = re.findall(r"\d+", msg)
        if not nums:
            return "Please specify loan amount, e.g., 'Request loan 500000'."
        loan_amt = float(nums[0])
        pre_limit = customer["income"] * 12
        credit_score = customer["credit_score"]

        if credit_score < 700:
            return f"Loan rejected due to low credit score ({credit_score})."

        if loan_amt <= pre_limit:
            pdf_file = self.generate_sanction_letter(customer, loan_amt)
            return f"Loan approved instantly! Sanction letter generated: {pdf_file}"
        elif loan_amt <= 2 * pre_limit:
            return "Loan requires salary slip verification. Please upload salary slip (feature not implemented)."
        else:
            return "Loan rejected: requested amount exceeds maximum limit."

    # -------------------------
    # GENERATE PDF SANCTION LETTER
    # -------------------------
    def generate_sanction_letter(self, customer, loan_amt):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Tata Capital Loan Sanction Letter", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8,
                       f"Date: {datetime.now().strftime('%d-%m-%Y')}\n\n"
                       f"Customer Name: {customer['name']}\n"
                       f"Customer ID: {customer['cid']}\n"
                       f"Loan Amount Sanctioned: INR {loan_amt:.2f}\n"
                       f"Credit Score: {customer['credit_score']}\n\n"
                       "Congratulations! Your loan has been sanctioned as per our terms and conditions."
                       )
        file_name = os.path.join(SANCTION_DIR, f"Sanction_{customer['cid']}.pdf")
        pdf.output(file_name)
        return file_name
