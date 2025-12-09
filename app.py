import streamlit as st
from chatbot import create_customer, get_customer_by_cid, MasterAgent
import time
import os

st.set_page_config(page_title="Tata Loan Assistant", layout="centered")

# --- Init session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False
if "agent" not in st.session_state:
    st.session_state.agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "_last_processed_input" not in st.session_state:
    st.session_state._last_processed_input = None
if "_last_input_time" not in st.session_state:
    st.session_state._last_input_time = 0.0
if "processing" not in st.session_state:
    st.session_state.processing = False

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
    if st.session_state.logged_in:
        chat_page()
        return

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
                st.session_state._last_input_time = 0.0
                st.session_state.processing = False
                st.success("Logged in")
                st.rerun()
            else:
                st.error("Invalid credentials")
    with col2:
        if st.button("Create New Account"):
            st.session_state.show_signup = True
            st.rerun()

    if st.session_state.show_signup:
        signup_page()

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
            st.success(f"Account created. Customer ID: {cid}")
            st.session_state.show_signup = False
            st.rerun()

    if st.button("Back to Login"):
        st.session_state.show_signup = False
        st.rerun()

def chat_page():
    header()
    if st.session_state.agent is None:
        st.error("Agent not configured — please log in again.")
        return

    # Show chat history
    for sender, msg in st.session_state.chat_history:
        if sender == "bot":
            st.chat_message("assistant").markdown(msg)
        else:
            st.chat_message("user").write(msg)

    # ✅ PDF Download Button - Shows when available
    agent = st.session_state.agent
    if getattr(agent, "last_sanction_path", None):
        pdf_path = agent.last_sanction_path
        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("**🎉 Download your sanction letter below:**")
            with col2:
                st.download_button(
                    label=f"📄 Download PDF",
                    data=pdf_bytes,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf"
                )
            st.markdown("---")
        except Exception as e:
            st.error(f"PDF Error: {e}")
        agent.last_sanction_path = None

    # Processing flag prevents duplicates
    if st.session_state.processing:
        st.info("🤖 Processing your message...")
        st.chat_input(disabled=True, label_visibility="collapsed")
    else:
        user_msg = st.chat_input("Type your message here...")

        if user_msg:
            if user_msg != st.session_state._last_processed_input:
                st.session_state.processing = True
                st.session_state._last_processed_input = user_msg
                
                # Show user message
                append_user(user_msg)
                st.chat_message("user").write(user_msg)
                
                # Bot response
                with st.chat_message("assistant"):
                    with st.spinner("Tata Capital is processing..."):
                        reply = st.session_state.agent.reply(user_msg)
                        st.markdown(reply)
                        append_bot(reply)
                
                st.session_state.processing = False
                st.rerun()

    if st.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.show_signup = False
        st.session_state.chat_history = []
        st.session_state.agent = None
        st.session_state._last_processed_input = None
        st.session_state.processing = False
        st.success("Logged out")
        st.rerun()

# ---------- Router ----------
def main():
    if st.session_state.logged_in:
        chat_page()
    elif st.session_state.show_signup:
        signup_page()
    else:
        login_page()

if __name__ == "__main__":
    main()

