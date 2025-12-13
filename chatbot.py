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
            if row.get("customer_id") == str(cid):
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
    def __init__(self, cid):
        self.cid = cid
        self.state = "idle"
        self.temp = {}
        self.last_sanction_path = None

    def start_chat(self):
        self.state = "idle"
        self.temp = {}
        self.last_sanction_path = None
        return "Hello! I'm your Tata Capital Loan Assistant. Type **'Apply loan'** to begin or **'Check eligibility'**."

    def reply(self, message):
        text = str(message).strip().lower()

        # Quick commands
        if text in ("offers", "show offers", "discounts"):
            return self._show_offers()
        if self.state == "idle" and "elig" in text:
            return self._quick_eligibility()

        # Idle state
        if self.state == "idle":
            if any(word in text for word in ["apply", "loan", "start"]):
                self.state = "ask_amount"
                return "Sure — what loan amount do you need?"
            return "Type **'Apply loan'** to start or **'Check eligibility'**."

        # Ask loan amount
        if self.state == "ask_amount":
            amt = self._parse_number(text)
            if amt is None or amt <= 0:
                return "Please enter a valid numeric loan amount."
            self.temp["loan_amount"] = float(amt)
            self.state = "ask_tenure"
            return "Enter tenure in months (6–84)."

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

        if self.state == "ask_name":
            if not re.search(r"[A-Za-z]", text):
                return "Name seems invalid — enter your Full Name."
            self.temp["full_name"] = text.title()
            self.state = "ask_dob"
            return "Enter Date of Birth (DD-MM-YYYY)."

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

        if self.state == "ask_id":
            if len(text) < 6:
                return "Enter valid PAN/Aadhaar (at least 6 chars)."
            self.temp["id_number"] = text
            self.state = "ask_income"
            return "Enter monthly income."

        if self.state == "ask_income":
            inc = self._parse_number(text)
            if inc is None or inc <= 0:
                return "Enter monthly income as a number."
            self.temp["income"] = float(inc)
            self.state = "ask_employment"
            return "Employment Type? (**Salaried** / **Self-Employed**)"

        if self.state == "ask_employment":
            if "salar" in text:
                self.temp["employment"] = "Salaried"
            elif "self" in text:
                self.temp["employment"] = "Self-Employed"
            else:
                return "Please reply **'Salaried'** or **'Self-Employed'**."
            self.state = "ask_existing_emi"
            return "Existing EMI (0 if none)?"

        if self.state == "ask_existing_emi":
            emi = self._parse_number(text)
            if emi is None or emi < 0:
                return "Enter existing EMI as a number (0 if none)."
            self.temp["existing_emi"] = float(emi)
            # run final check - but possibly request salary slip
            return self._final_check()

        if self.state == "confirm":
            if text in ("yes", "y"):
                return self._do_sanction()
            else:
                self.state = "idle"
                self.temp = {}
                return "❌ Application cancelled."

        if self.state == "await_salary_upload":
            # user typed while waiting for upload - remind them to upload
            return "Please upload your salary slip using the upload box shown by the assistant."

        return "I didn't understand. Please follow the prompts."

    def process_salary_upload(self, file_bytes, filename):
        """
        Called by the UI after the user uploads a salary slip file.
        Performs a semi-detailed validation:
        - Try to extract numbers from filename and file bytes (simulated OCR).
        - If no numeric salary can be read, assume match (simulate OCR success).
        - Accept if extracted_salary within ±15% of registered monthly_income.
        """
        # Ensure we were actually expecting an upload
        if self.state != "await_salary_upload":
            return "No salary slip required at this time."

        master = get_customer_by_cid(self.cid)
        registered_income = master.get("income", 0) if master else self.temp.get("income", 0)

        # try extract numeric salary from filename
        nums = re.findall(r"\d{3,9}", filename or "")
        extracted_salary = None
        if nums:
            # take the largest number found (likely the salary figure)
            extracted_salary = float(max(nums, key=len))
        else:
            # try to decode bytes and search for numbers (best-effort)
            try:
                text = None
                # try common encodings
                for enc in ("utf-8", "latin-1", "iso-8859-1"):
                    try:
                        text = file_bytes.decode(enc)
                        break
                    except:
                        text = None
                if text:
                    nums2 = re.findall(r"\d{3,9}", text)
                    if nums2:
                        extracted_salary = float(max(nums2, key=len))
            except:
                extracted_salary = None

        # If no number found at all, assume OCR matched the registered income (simulate)
        if extracted_salary is None:
            extracted_salary = float(registered_income)

        # Compare within +/- 15%
        if registered_income <= 0:
            self.state = "idle"
            self.temp = {}
            return "Unable to validate salary: registered income missing."

        diff_pct = abs(extracted_salary - registered_income) / registered_income
        if diff_pct > 0.15:
            # mismatch - reject
            self.state = "idle"
            self.temp = {}
            return (
                f"❌ Salary slip validation failed.\n"
                f"Detected salary ₹{extracted_salary:,.0f} does not match registered income ₹{registered_income:,.0f} (>{diff_pct*100:.0f}% difference)."
            )

        # Salary slip accepted — re-run EMI affordability check as in _final_check
        loan = self.temp.get("loan_amount")
        months = self.temp.get("tenure")
        income = registered_income
        existing = self.temp.get("existing_emi", 0)
        emi = self._compute_emi(loan, months)
        allowed = max(0, 0.5 * income - existing)

        if emi > allowed:
            self.state = "idle"
            self.temp = {}
            return f"❌ **Loan rejected after salary verification**: EMI ₹{emi:.0f} exceeds allowed ₹{allowed:.0f}."

        # Passed — set temp and move to confirmation
        self.temp["emi"] = emi
        self.state = "confirm"
        return (
            f"✅ Salary slip verified. \n\n"
            f"💰 **Loan**: INR {loan:,.0f}\n"
            f"📅 **Tenure**: {months} months\n"
            f"💳 **EMI**: INR {emi:,.0f}\n\n"
            f"**Do you want to proceed?** (yes/no)"
        )

    def _do_sanction(self):
        master = get_customer_by_cid(self.cid)
        if not master:
            self.state = "idle"
            return "Master profile missing."

        pdf_path = generate_sanction_pdf(master, self.temp, self.temp["loan_amount"], self.temp["tenure"], self.temp["emi"])
        self.last_sanction_path = pdf_path
        
        pdf_filename = os.path.basename(pdf_path)
        self.state = "idle"
        self.temp = {}
        return f"🎉 **Loan sanctioned successfully!**\n\n**📄 {pdf_filename}**\n\n**Download button appears below the chat!**\n\nThank you for choosing Tata Capital! 🎊"

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
        return f"✅ **Credit score**: {c['credit_score']}\n💰 **Pre-approved**: INR {limit:,.0f}"

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

        # New rule: if loan is "large" compared to registered income, ask for salary slip.
        # We use a realistic threshold: require slip when loan > 20 * monthly_income.
        registered_income = master.get("income", income)
        if registered_income and loan > 20 * registered_income:
            # Ask user to upload salary slip.
            self.state = "await_salary_upload"
            # store temp values for later use when the slip is uploaded
            self.temp["emi"] = emi
            return (
                "Your requested loan amount is large compared to your registered income. "
                "Please upload your salary slip to proceed. [[UPLOAD_SALARY_SLIP]]"
            )

        if score < 700:
            self.state = "idle"
            self.temp = {}
            return f"❌ **Loan rejected**: credit score {score} below minimum."

        if emi > allowed:
            self.state = "idle"
            self.temp = {}
            return f"❌ **Loan rejected**: EMI ₹{emi:.0f} exceeds allowed ₹{allowed:.0f}."

        self.temp["emi"] = emi
        self.state = "confirm"
        return (
            f"✅ **Eligible for loan!**\n\n"
            f"💰 **Loan**: INR {loan:,.0f}\n"
            f"📅 **Tenure**: {months} months\n"
            f"💳 **EMI**: INR {emi:,.0f}\n"
            f"⭐ **Credit score**: {score}\n\n"
            f"**Do you want to proceed?** (yes/no)"
        )

    def _show_offers(self):
        return "🔥 **Current Offers**:\n• Personal Loan @11% p.a.\n• Women special -0.5%\n• Fee discount above ₹300k"
