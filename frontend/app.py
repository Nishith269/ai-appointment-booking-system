import streamlit as st
import requests
from datetime import datetime, date, time
import uuid

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

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
    res = requests.post(API_URL, json={
        "message": query,
        "thread_id": st.session_state.get("thread_id", "1")
    })
    return res.json()["response"]


def get_booked_slots():
    res = requests.post(API_URL, json={
        "message": "List all appointments",
        "thread_id": st.session_state.get("thread_id")
    })

    text = res.json().get("response", "")

    # Extract datetime from response (basic parsing)
    import re
    matches = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', text)

    import datetime
    booked = [datetime.datetime.strptime(m, "%Y-%m-%d %H:%M:%S") for m in matches]

    return booked

def book_direct(date, time, name):
    res = requests.post("http://127.0.0.1:8000/book", json={
        "date": str(date),
        "time": str(time),
        "name": name
    })
    return res.json()["response"]

def cancel_direct(date, time):
    res = requests.post("http://127.0.0.1:8000/cancel", json={
        "date": str(date),
        "time": str(time)
    })
    return res.json()["response"]

def list_direct():
    res = requests.post("http://127.0.0.1:8000/list")
    return res.json()["response"]

def next_direct():
    res = requests.post("http://127.0.0.1:8000/next")
    return res.json()["response"]

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2 = st.tabs(["💬 Chat", "⚙️ Actions"])

# -----------------------------
# CHAT TAB
# -----------------------------
with tab1:
    st.subheader("💬 Chat with AI")

    user_input = st.text_input("Type your message")

    if st.button("Send"):
        if user_input:
            response = send_query(user_input)

            st.session_state.chat_history.append(("You", user_input))
            st.session_state.chat_history.append(("Bot", response))

    for role, msg in st.session_state.chat_history:
        with st.chat_message("user" if role == "You" else "assistant"):
            st.write(msg)

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

        selected_date = st.date_input(
            "Select date",
            value=None,
            min_value=date.today()
        )

        selected_time = None

        if selected_date is not None:
            now = datetime.now()
            booked_slots = get_booked_slots()

            time_options = []

            for hour in range(24):
                for minute in (0, 30):
                    slot = datetime.combine(selected_date, time(hour, minute))

                    if slot <= now:
                        continue

                    if any(abs((slot - b).total_seconds()) < 60 for b in booked_slots):
                        continue

                    time_options.append(time(hour, minute))

            if not time_options:
                st.error("❌ No available slots for this day.")
            else:
                selected_time = st.selectbox(
                    "Select time",
                    ["-- Select Time --"] + time_options
                )

        if st.button("Confirm Booking"):
            if not name:
                st.warning("Please enter your name")
            elif selected_date is None:
                st.warning("Please select a date")
            elif selected_time == "-- Select Time --" or selected_time is None:
                st.warning("Please select a time")
            else:
                response = book_direct(selected_date, selected_time, name)
                st.success(response)

    # ---------------- CANCEL ----------------
    elif action == "Cancel Appointment":
        st.info("Please select the date and time of the appointment you want to cancel.")

        # Session state for confirmation flow
        if "confirm_cancel" not in st.session_state:
            st.session_state.confirm_cancel = False

        if "cancel_payload" not in st.session_state:
            st.session_state.cancel_payload = None

        cancel_date = st.date_input(
            "Cancel date",
            value=None,
            min_value=date.today()
        )

        cancel_time = st.selectbox(
            "Cancel time",
            ["-- Select Time --"] + [time(h, m) for h in range(24) for m in (0, 30)]
        )

        # Step 1: User clicks cancel → store selection + trigger confirmation UI
        if st.button("Cancel Appointment"):
            if cancel_date is None:
                st.warning("Please select a date")
            elif cancel_time == "-- Select Time --":
                st.warning("Please select a time")
            else:
                st.session_state.confirm_cancel = True
                st.session_state.cancel_payload = (cancel_date, cancel_time)

        # Step 2: Show confirmation UI (popup-like)
        if st.session_state.confirm_cancel:
            st.warning("⚠️ Are you sure you want to cancel this appointment?")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Yes, Cancel"):
                    date_val, time_val = st.session_state.cancel_payload
                    response = cancel_direct(date_val, time_val)

                    st.success(response)

                    # Reset state
                    st.session_state.confirm_cancel = False
                    st.session_state.cancel_payload = None

            with col2:
                if st.button("No"):
                    st.session_state.confirm_cancel = False
                    st.session_state.cancel_payload = None

    # ---------------- NEXT SLOT ----------------
    elif action == "Next Available Slot":
        if st.button("Get Next Slot"):
            response = next_direct()
            st.info(response)

    # ---------------- LIST ----------------
    elif action == "List Appointments":
        if st.button("Show Appointments"):
            response = list_direct()
            st.write(response)