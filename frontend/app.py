import streamlit as st
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(page_title="AI Appointment Assistant", layout="centered")

st.title("📅 AI Appointment Booking Assistant")

# -----------------------------
# Session state for chat history
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# Function to call backend
# -----------------------------
def send_query(query):
    res = requests.post(API_URL, json={"message": query, "thread_id": "1"})
    return res.json()["response"]

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2 = st.tabs(["💬 Chat", "⚙️ Actions"])

# -----------------------------
# CHAT TAB
# -----------------------------
with tab1:
    user_input = st.text_input("Ask anything about appointments")

    if st.button("Send"):
        if user_input:
            response = send_query(user_input)

            st.session_state.chat_history.append(("You", user_input))
            st.session_state.chat_history.append(("Bot", response))

    # Display chat history
    for role, msg in st.session_state.chat_history:
        if role == "You":
            st.markdown(f"**🧑 You:** {msg}")
        else:
            st.markdown(f"**🤖 Bot:** {msg}")

# -----------------------------
# ACTION TAB
# -----------------------------
with tab2:
    st.subheader("📌 Quick Actions")

    action = st.selectbox(
        "Choose action",
        ["Book Appointment", "Cancel Appointment", "Next Available Slot", "List Appointments"]
    )

    # ---------------- BOOK ----------------
    if action == "Book Appointment":
        name = st.text_input("Enter your name")
        date = st.date_input("Select date")
        time = st.time_input("Select time")

        if st.button("Confirm Booking"):
            query = f"Book an appointment for {name} on {date} at {time}"
            response = send_query(query)
            st.success(response)

    # ---------------- CANCEL ----------------
    elif action == "Cancel Appointment":
        st.write("You can specify or leave blank to let AI decide.")

        date = st.date_input("Cancel date", key="cancel_date")
        time = st.time_input("Cancel time", key="cancel_time")

        if st.button("Cancel Appointment"):
            query = f"Cancel appointment on {date} at {time}"
            response = send_query(query)
            st.warning(response)

    # ---------------- NEXT SLOT ----------------
    elif action == "Next Available Slot":
        if st.button("Get Next Slot"):
            response = send_query("What is the next available appointment?")
            st.info(response)

    # ---------------- LIST ----------------
    elif action == "List Appointments":
        if st.button("Show Appointments"):
            response = send_query("List all appointments")
            st.write(response)