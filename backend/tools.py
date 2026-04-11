import datetime
from langchain_core.tools import tool

# In-memory storage for appointments
# NOTE: This can be replaced with a real database later (MongoDB/PostgreSQL)
APPOINTMENTS = []

@tool
def get_next_appointment():
    """Returns the next available UNBOOKED 30-min slot"""
    import datetime

    now = datetime.datetime.now()

    # Round to next 30-min slot
    minutes = (30 - now.minute % 30) % 30
    if minutes == 0:
        minutes = 30

    next_slot = now + datetime.timedelta(minutes=minutes)
    next_slot = next_slot.replace(second=0, microsecond=0)

    # Loop until we find unbooked slot
    while any(appointment["time"] == next_slot for appointment in APPOINTMENTS):
        next_slot += datetime.timedelta(minutes=30)

    return f"The next available appointment is at {next_slot}"

@tool
def book_appointment(
    year: int = None,
    month: int = None,
    day: int = None,
    hour: int = None,
    minute: int = None,
    client_name: str = None
):
    """
    Books an appointment if the slot is available, Requires all fields.

    Args:
        year, month, day, hour, minute → appointment time
        client_name → name of the user 

    """

    import datetime

    # ❌ Missing fields → ask user
    if not client_name:
        return "Please provide your name to book the appointment."

    if not all([year, month, day]):
        return "Please provide the date for the appointment."

    if hour is None or minute is None:
        return "Please provide the time for the appointment (30-minute slots only)."

    time = datetime.datetime(year, month, day, hour, minute)
    now = datetime.datetime.now()

    # ❌ Past booking
    if time < now:
        return "You cannot book an appointment in the past. Please choose a future time."

    # ❌ Enforce 30-min slots
    if minute not in [0, 30]:
        return "Appointments can only be booked at 30-minute intervals (e.g., 11:00, 11:30)."

    # ❌ Conflict check
    for appointment in APPOINTMENTS:
        if appointment["time"] == time:
            return f"Appointment at {time} is already booked"

    APPOINTMENTS.append({"time": time, "name": client_name})
    return f"Appointment successfully booked for {time}"


@tool
def cancel_appointment(index: int = None, year: int = None, month: int = None, day: int = None, hour: int = None, minute: int = None):
    """Cancel appointment by index OR by datetime."""

    import datetime

    # ✅ Cancel by index
    if index is not None:
        if index < 1 or index > len(APPOINTMENTS):
            return "Invalid selection."

        removed = APPOINTMENTS.pop(index - 1)
        return f"Cancelled {removed['name']} at {removed['time']}"

    # Existing logic (datetime-based)
    if not all([year, month, day, hour, minute]):
        if not APPOINTMENTS:
            return "There are no appointments to cancel."

        return "Please select which appointment to cancel:\n" + "\n".join(
            [f"{i+1}. {appt['name']} at {appt['time']}" for i, appt in enumerate(APPOINTMENTS)]
        )

    time = datetime.datetime(year, month, day, hour, minute)

    for appointment in APPOINTMENTS:
        if appointment["time"] == time:
            APPOINTMENTS.remove(appointment)
            return f"Appointment at {time} cancelled"

    return "No matching appointment found."


@tool
def list_appointments():
    """Displays all booked appointments."""
    if not APPOINTMENTS:
        return "There are no appointments scheduled."

    return "\n".join([
        f"{i+1}. {appointment['name']} at {appointment['time']}"
        for i, appointment in enumerate(APPOINTMENTS)
    ])