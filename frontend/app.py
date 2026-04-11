import streamlit as st
import requests
from datetime import datetime, date, time

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


def get_booked_slots():
    res = requests.post(API_URL, json={
        "message": "List all appointments",
        "thread_id": "1"
    })

    text = res.json().get("response", "")

    # Extract datetime from response (basic parsing)
    import re
    matches = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', text)

    import datetime
    booked = [datetime.datetime.strptime(m, "%Y-%m-%d %H:%M:%S") for m in matches]

    return booked

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

        selected_date = st.date_input(
            "Select date",
            value=None,
            min_value=date.today()
        )

        now = datetime.now()
        time_options = []

        if selected_date is not None:
            now = datetime.now()

            # Get booked slots
            booked_slots = get_booked_slots()

            for hour in range(24):
                for minute in (0, 30):
                    slot = datetime.combine(
                        selected_date,
                        time(hour, minute)
                    )

                    # Only future slots
                    if slot <= now:
                        continue

                    # Remove booked slots
                    if any(abs((slot - b).total_seconds()) < 60 for b in booked_slots):
                        continue

                    time_options.append(time(hour, minute))


        
        if selected_date is None:
            st.warning("Please select a date first")
            time = None

        # 🚫 No slots left for the day
        elif not time_options:
            st.error("❌ No available slots for this day. Please select another date.")
            time = None

        else:
            time = st.selectbox("Select time", ["-- Select Time --"] + time_options)

        # Booking button
        
        if st.button("Confirm Booking"):
            if not name:
                st.warning("Please enter your name")
            elif selected_date is None:
                st.warning("Please select a date")
            elif time == "-- Select Time --":
                st.warning("Please select a time")
            else:
                query = f"Book an appointment for {name} on {selected_date} at {time}"
                response = send_query(query)
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

                    query = f"CONFIRMED: Cancel appointment on {date_val} at {time_val}"
                    response = send_query(query)

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
            response = send_query("What is the next available appointment?")
            st.info(response)

    # ---------------- LIST ----------------
    elif action == "List Appointments":
        if st.button("Show Appointments"):
            response = send_query("List all appointments")
            st.write(response)