import streamlit as st
import requests
from datetime import datetime, date, time
import uuid

# -----------------------------
# Session Setup
# -----------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Appointment Assistant", layout="centered")
st.title("📅 AI Appointment Booking Assistant")

# -----------------------------
# Safe API Call
# -----------------------------
def safe_post(url, payload=None):
    try:
        res = requests.post(url, json=payload)

        if res.status_code != 200:
            st.error(f"API Error: {res.status_code}")
            return None

        return res.json()

    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None


# -----------------------------
# Chat API
# -----------------------------
def send_query(query):
    data = safe_post(f"{API_BASE}/chat", {
        "message": query,
        "thread_id": st.session_state.thread_id
    })

    if data:
        return data.get("response", "No response")
    return "Error occurred"


# -----------------------------
# Direct APIs
# -----------------------------
def book_direct(date_val, time_val, name):
    data = safe_post(f"{API_BASE}/book", {
        "date": str(date_val),
        "time": str(time_val),
        "name": name
    })
    return data.get("response", "Error") if data else "Error"


def cancel_direct_by_id(appt_id):
    data = safe_post(f"{API_BASE}/cancel", {
        "id": appt_id
    })
    return data.get("response", "Error") if data else "Error"


def list_direct():
    data = safe_post(f"{API_BASE}/list")
    return data.get("appointments", []) if data else []


def next_direct():
    data = safe_post(f"{API_BASE}/next")
    return data.get("response", "Error") if data else "Error"


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
        st.caption("Fields marked with * are mandatory")

        name = st.text_input("Enter your name *")

        selected_date = st.date_input(
            "Select date *",
            value=None,
            min_value=date.today()
        )

        selected_time = None

        if selected_date is not None:
            now = datetime.now()
            appointments = list_direct()

            booked_slots = [
                datetime.strptime(a["time"], "%Y-%m-%d %H:%M:%S")
                for a in appointments
            ]

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
                    "Select time *",
                    ["-- Select Time --"] + time_options
                )

        # Inline validation hints
        if not name:
            st.caption("⚠️ Please enter your name")
        if selected_date is None:
            st.caption("⚠️ Please select a date")
        if selected_time in [None, "-- Select Time --"]:
            st.caption("⚠️ Please select a time")

        is_valid = (
            name and
            selected_date is not None and
            selected_time not in [None, "-- Select Time --"]
        )

        if st.button("Confirm Booking", disabled=not is_valid):
            response = book_direct(selected_date, selected_time, name)

            if "error" in response.lower():
                st.error(response)
            else:
                st.success(response)

    # ---------------- CANCEL ----------------
    elif action == "Cancel Appointment":
        st.caption("Select an appointment to cancel *")

        appointments = list_direct()

        if not appointments:
            st.warning("No appointments to cancel.")
        else:
            options = [
                f"{a['client_name']} at {a['time']}"
                for a in appointments
            ]

            selected = st.selectbox("Choose appointment *", options)

            is_valid = selected is not None

            if st.button("Cancel Appointment", disabled=not is_valid):
                idx = options.index(selected)
                appt_id = appointments[idx]["id"]

                response = cancel_direct_by_id(appt_id)

                if "error" in response.lower():
                    st.error(response)
                else:
                    st.success(response)

    # ---------------- NEXT ----------------
    elif action == "Next Available Slot":
        if st.button("Get Next Slot"):
            response = next_direct()

            if "error" in response.lower():
                st.error(response)
            else:
                st.info(response)

    # ---------------- LIST ----------------
    elif action == "List Appointments":
        if st.button("Show Appointments"):
            appointments = list_direct()

            if not appointments:
                st.info("No appointments found.")
            else:
                for a in appointments:
                    st.write(f"• {a['client_name']} at {a['time']}")