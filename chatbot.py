# chatbot.py
import csv
import os
import random
import re
from datetime import datetime
from sanction_generator import generate_sanction_pdf

CUSTOMER_FILE = "customers.csv"

# Ensure customer file exists
if not os.path.isfile(CUSTOMER_FILE):
    with open(CUSTOMER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "customer_id", "name", "password", "monthly_income", "age",
            "employment_type", "existing_emi", "credit_score"
        ])

# ------------------ Customer Functions ------------------
def create_customer(name, password, income, age, employment):
    cid = str(100000 + random.randint(1, 899999))
    credit_score = random.randint(650, 850)
    with open(CUSTOMER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([cid, name, password, income, age, employment, 0, credit_score])
    return cid

def get_customer_by_cid(cid):
    if not os.path.isfile(CUSTOMER_FILE):
        return None
    with open(CUSTOMER_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("customer_id") == cid:
                return {
                    "cid": row["customer_id"],
                    "name": row["name"],
                    "password": row["password"],
                    "income": float(row.get("monthly_income") or 0),
                    "age": int(row.get("age") or 0),
                    "employment": row.get("employment_type"),
                    "existing_emi": float(row.get("existing_emi") or 0),
                    "credit_score": int(row.get("credit_score") or 0),
                }
    return None

# ------------------ Master Agent ------------------
class MasterAgent:
    """
    Deterministic FSM for loan flow:
    idle -> ask_amount -> ask_tenure -> ask_name -> ask_dob -> ask_id -> ask_income -> ask_employment -> ask_existing_emi -> confirm -> sanction
    """
    def __init__(self, cid):
        self.cid = cid
        self.state = "idle"
        self.temp = {}
        self.last_sanction_path = None

    # Start chat
    def start_chat(self):
        self.state = "idle"
        self.temp = {}
        self.last_sanction_path = None
        return "Hello! I'm your Tata Capital Loan Assistant. Type 'Apply loan' to begin or 'Check eligibility'."

    # Main reply function
    def reply(self, message):
        text = str(message).strip()

        # Quick commands
        if text.lower() in ("offers", "show offers", "discounts"):
            return self._show_offers()
        if self.state == "idle" and "elig" in text.lower():
            return self._quick_eligibility()

        # Idle state
        if self.state == "idle":
            if "apply" in text.lower():
                self.state = "ask_amount"
                return "Sure — what loan amount do you need?"
            return "Type 'Apply loan' to start or 'Check eligibility'."

        # Ask loan amount
        if self.state == "ask_amount":
            amt = self._parse_number(text)
            if amt is None or amt <= 0:
                return "Please enter a valid numeric loan amount."
            self.temp["loan_amount"] = float(amt)
            self.state = "ask_tenure"
            return "Enter tenure in months (6–84)."

        # Ask tenure
        if self.state == "ask_tenure":
            months = self._parse_number(text)
            if months is None:
                return "Enter tenure as number (6–84)."
            months = int(months)
            if months < 6 or months > 84:
                return "Tenure must be between 6 and 84 months."
            self.temp["tenure"] = months
            self.state = "ask_name"
            return "Enter your Full Name (as per KYC)."

        # Ask full name
        if self.state == "ask_name":
            if not re.search(r"[A-Za-z]", text):
                return "Name seems invalid — enter your Full Name."
            self.temp["full_name"] = text
            self.state = "ask_dob"
            return "Enter Date of Birth (DD-MM-YYYY)."

        # Ask DOB
        if self.state == "ask_dob":
            try:
                dt = datetime.strptime(text, "%d-%m-%Y")
                if dt.year < 1900 or dt > datetime.now():
                    return "DOB seems invalid."
            except:
                return "Invalid DOB format. Use DD-MM-YYYY."
            self.temp["dob"] = text
            self.state = "ask_id"
            return "Enter PAN or Aadhaar number."

        # Ask ID
        if self.state == "ask_id":
            if len(text) < 6:
                return "Enter valid PAN/Aadhaar (at least 6 chars)."
            self.temp["id_number"] = text
            self.state = "ask_income"
            return "Enter monthly income."

        # Ask income
        if self.state == "ask_income":
            inc = self._parse_number(text)
            if inc is None or inc <= 0:
                return "Enter monthly income as a number."
            self.temp["income"] = float(inc)
            self.state = "ask_employment"
            return "Employment Type? (Salaried / Self-Employed)"

        # Ask employment
        if self.state == "ask_employment":
            low = text.lower()
            if "salar" in low:
                self.temp["employment"] = "Salaried"
            elif "self" in low:
                self.temp["employment"] = "Self-Employed"
            else:
                return "Please reply 'Salaried' or 'Self-Employed'."
            self.state = "ask_existing_emi"
            return "Existing EMI (0 if none)?"

        # Ask existing EMI
        if self.state == "ask_existing_emi":
            emi = self._parse_number(text)
            if emi is None or emi < 0:
                return "Enter existing EMI as a number (0 if none)."
            self.temp["existing_emi"] = float(emi)
            return self._final_check()

        # Confirm sanction
        if self.state == "confirm":
            if text.lower() in ("yes", "y"):
                return self._do_sanction()
            else:
                self.state = "idle"
                self.temp = {}
                return "Application cancelled."

        return "I didn't understand. Please follow the prompts."

    # ---------- Helpers ----------
    def _parse_number(self, txt):
        cleaned = re.sub(r"[^\d.]", "", txt)
        if cleaned == "":
            return None
        try:
            return float(cleaned)
        except:
            return None

    def _quick_eligibility(self):
        c = get_customer_by_cid(self.cid)
        if not c:
            return "No profile found. Signup first."
        limit = c["income"] * 12
        return f"Credit score: {c['credit_score']} • Approx pre-approved: INR {limit:.0f}"

    def _compute_emi(self, principal, months, rate=11.0):
        r = rate / 100 / 12
        if months <= 0:
            return 0
        return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)

    def _final_check(self):
        loan = self.temp["loan_amount"]
        months = self.temp["tenure"]
        income = self.temp["income"]
        existing = self.temp.get("existing_emi", 0)
        master = get_customer_by_cid(self.cid) or {}
        score = master.get("credit_score", random.randint(650, 820))

        emi = self._compute_emi(loan, months)
        allowed = max(0, 0.5 * income - existing)

        if score < 700:
            self.state = "idle"
            self.temp = {}
            return f"Loan rejected: credit score {score} below minimum."

        if emi > allowed:
            self.state = "idle"
            self.temp = {}
            return f"Loan rejected: EMI {emi:.0f} exceeds allowed {allowed:.0f}."

        self.temp["emi"] = emi
        self.state = "confirm"
        return (
            f"Eligible!\nLoan: INR {loan:.0f}\nTenure: {months} months\n"
            f"Estimated EMI: INR {emi:.0f}\nCredit score: {score}\n"
            "Do you want to proceed? (yes/no)"
        )

    def _do_sanction(self):
        master = get_customer_by_cid(self.cid)
        if not master:
            self.state = "idle"
            return "Master profile missing."

        pdf_path = generate_sanction_pdf(master, self.temp, self.temp["loan_amount"], self.temp["tenure"], self.temp["emi"])
        self.last_sanction_path = pdf_path
        self.state = "idle"
        self.temp = {}
        return f"🎉 Loan sanctioned! Download: {os.path.basename(pdf_path)}"

    def _show_offers(self):
        return "Offers: Personal Loan @11% p.a. / Women special -0.5% / Fee discount above 300k"

