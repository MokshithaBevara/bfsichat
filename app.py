import streamlit as st
from chatbot import get_customer_by_cid, create_customer, MasterAgent

# -------------------------
# PAGE HEADER
# -------------------------
def header():
    st.markdown("## 🏦 BFSI Smart Loan Assistant")

# -------------------------
# LOGIN PAGE
# -------------------------
def login_page():
    header()
    cid = st.text_input("Customer ID")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        cust = get_customer_by_cid(cid)
        if cust and cust["password"] == pwd:
            st.session_state.logged_in = True
            st.session_state.customer_id = cid
            st.session_state.agent = MasterAgent(cid)
            st.session_state.chat_history = [("bot", st.session_state.agent.start_chat())]
            st.success("Logged in")
        else:
            st.error("Invalid credentials")

    st.markdown("---")

    if st.button("Create New Account"):
        st.session_state.show_signup = True


# -------------------------
# SIGNUP PAGE
# -------------------------
def signup_page():
    header()
    name = st.text_input("Full Name")
    password = st.text_input("Create Password", type="password")
    income = st.number_input("Monthly Income", min_value=0)
    age = st.number_input("Age", min_value=18)
    employment = st.selectbox("Employment Type", ["Salaried", "Self-Employed"])

    if st.button("Create Account"):
        cid = create_customer(name, password, income, age, employment)
        st.success(f"Account created! Your Customer ID is {cid}")
        st.session_state.show_signup = False
        st.session_state.logged_in = True
        st.session_state.customer_id = cid
        st.session_state.agent = MasterAgent(cid)
        st.session_state.chat_history = [("bot", st.session_state.agent.start_chat())]

    if st.button("Back to Login"):
        st.session_state.show_signup = False


# -------------------------
# CHAT PAGE
# -------------------------
def chat_page():
    header()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat messages
    for sender, msg in st.session_state.chat_history:
        if sender == "bot":
            st.chat_message("assistant").write(msg)
        else:
            st.chat_message("user").write(msg)

    # Input message
    user_msg = st.chat_input("Type your message")
    if user_msg:
        st.session_state.chat_history.append(("user", user_msg))
        bot_reply = st.session_state.agent.reply(user_msg)
        st.session_state.chat_history.append(("bot", bot_reply))

    # Logout button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.show_signup = False
        st.session_state.chat_history = []
        st.session_state.customer_id = None
        st.session_state.agent = None


# -------------------------
# MAIN
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False
if "customer_id" not in st.session_state:
    st.session_state.customer_id = None
if "agent" not in st.session_state:
    st.session_state.agent = None

# Page routing
if st.session_state.logged_in:
    chat_page()
elif st.session_state.show_signup:
    signup_page()
else:
    login_page()
