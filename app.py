# app.py (FIXED: Signup & Login show Customer ID; Go to Chat click; salary warning handled)
import streamlit as st
from chatbot import create_customer, get_customer_by_cid, MasterAgent
import os

st.set_page_config(page_title="Tata Loan Assistant", layout="centered")

# --- Init session state ---
for key, default in {
    "logged_in": False,
    "show_signup": False,
    "agent": None,
    "chat_history": [],
    "_last_processed_input": None,
    "_last_input_time": 0.0,
    "processing": False,
    "awaiting_upload": False,
    "customer_id": None,
    "show_chat_button": False,
    "signup_success": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- Helpers ----------
def header():
    st.markdown("## 🏦 Tata Capital Loan Assistant")
    st.markdown("---")

def append_user(msg):
    st.session_state.chat_history.append(("user", msg))

def append_bot(msg):
    st.session_state.chat_history.append(("bot", msg))

# ---------- Pages ----------
def login_page():
    header()

    if st.session_state.signup_success:
        st.success(f"Account created successfully! Customer ID: {st.session_state.signup_success}")
        st.session_state.signup_success = None

    cid = st.text_input("Customer ID", key="login_cid")
    pwd = st.text_input("Password", type="password", key="login_pwd")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            cust = get_customer_by_cid(cid)
            if cust and cust["password"] == pwd:
                st.session_state.logged_in = True
                st.session_state.customer_id = cid
                st.session_state.agent = MasterAgent(cid)
                st.session_state.chat_history = [("bot", st.session_state.agent.start_chat())]
                st.session_state._last_processed_input = None
                st.session_state.processing = False
                st.session_state.awaiting_upload = False
                st.session_state.show_chat_button = True
                st.success(f"Logged in successfully! Customer ID: {cid}")
            else:
                st.error("Invalid credentials")
    with col2:
        if st.button("Create New Account"):
            st.session_state.show_signup = True
            st.rerun()

    if st.session_state.show_signup:
        signup_page()

    # Show "Go to Chat" button only after successful login
    if st.session_state.show_chat_button:
        if st.button("Go to Chat"):
            st.session_state.show_chat_button = False
            chat_page()

def signup_page():
    header()
    st.markdown("### Create account")
    name = st.text_input("Full name", key="su_name")
    pwd = st.text_input("Password", type="password", key="su_pwd")
    income = st.number_input("Monthly income", min_value=0.0, key="su_income")
    age = st.number_input("Age", min_value=18, key="su_age")
    emp = st.selectbox("Employment", ["Salaried", "Self-Employed"], key="su_emp")

    if st.button("Create account"):
        if not name or not pwd:
            st.error("Enter name and password")
        else:
            cid = create_customer(name, pwd, income, age, emp)
            st.session_state.signup_success = cid
            st.session_state.show_signup = False
            st.rerun()

    if st.button("Back to Login"):
        st.session_state.show_signup = False
        st.rerun()

def chat_page():
    header()
    st.markdown(f"**Logged in as Customer ID:** {st.session_state.customer_id}")
    agent = st.session_state.agent

    # Show chat history
    for sender, msg in st.session_state.chat_history:
        if sender == "bot":
            st.chat_message("assistant").markdown(msg)
        else:
            st.chat_message("user").write(msg)

    # PDF Download
    if agent.last_sanction_path:
        pdf_path = agent.last_sanction_path
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label="📄 Download Sanction Letter",
            data=pdf_bytes,
            file_name=os.path.basename(pdf_path),
            mime="application/pdf",
        )
        agent.last_sanction_path = None

    # Salary slip uploader
    if agent.state == "await_salary_upload":
        st.session_state.awaiting_upload = True

    if st.session_state.awaiting_upload:
        st.info("📤 Please upload your salary slip (PDF/JPG/PNG).")
        uploaded_file = st.file_uploader(
            "Upload salary slip",
            type=["pdf", "jpg", "jpeg", "png"]
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            filename = uploaded_file.name

            with st.chat_message("assistant"):
                with st.spinner("Verifying salary slip..."):
                    reply = agent.process_salary_upload(file_bytes, filename)
                    # Show warning nicely if salary discrepancy
                    if "Salary discrepancy detected" in reply:
                        st.warning(reply)
                    else:
                        st.markdown(reply)
                    append_bot(reply)

            st.session_state.awaiting_upload = (agent.state == "await_salary_upload")
            st.rerun()

        st.chat_input(disabled=True)
        if st.button("Cancel Upload"):
            st.session_state.awaiting_upload = False
            agent.state = "idle"
            st.rerun()
        return

    # Normal chat input
    if st.session_state.processing:
        st.info("🤖 Processing your message…")
        st.chat_input(disabled=True)
    else:
        user_msg = st.chat_input("Type here…")
        if user_msg:
            st.session_state.processing = True
            append_user(user_msg)
            st.chat_message("user").write(user_msg)

            with st.chat_message("assistant"):
                with st.spinner("Tata Capital is processing…"):
                    reply = agent.reply(user_msg)
                    # Show salary discrepancy warning nicely
                    if "Salary discrepancy detected" in reply:
                        st.warning(reply)
                    else:
                        st.markdown(reply)
                    append_bot(reply)

            st.session_state.processing = False
            st.rerun()

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.agent = None
        st.session_state.chat_history = []
        st.session_state.customer_id = None
        st.session_state.show_chat_button = False
        st.rerun()

# ---------- Router ----------
def main():
    if st.session_state.logged_in and not st.session_state.show_chat_button:
        chat_page()
    elif st.session_state.show_signup:
        signup_page()
    else:
        login_page()

if __name__ == "__main__":
    main()

