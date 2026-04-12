import datetime
from langchain_core.tools import tool

from database import SessionLocal
from models import Appointment


# ---------------- GET NEXT AVAILABLE ----------------
@tool
def get_next_appointment():
    """Returns the next available UNBOOKED 30-min slot"""

    db = SessionLocal()
    try:
        now = datetime.datetime.now()

        # Round to next 30-min slot
        minutes = (30 - now.minute % 30) % 30
        if minutes == 0:
            minutes = 30

        next_slot = now + datetime.timedelta(minutes=minutes)
        next_slot = next_slot.replace(second=0, microsecond=0)

        # Find next unbooked slot
        while True:
            exists = db.query(Appointment).filter(Appointment.time == next_slot).first()
            if not exists:
                break
            next_slot += datetime.timedelta(minutes=30)

        return f"The next available appointment is at {next_slot}"

    finally:
        db.close()


# ---------------- BOOK ----------------
@tool
def book_appointment(
    year: int = None,
    month: int = None,
    day: int = None,
    hour: int = None,
    minute: int = None,
    client_name: str = None
):
    """Books an appointment if slot is available."""

    db = SessionLocal()
    try:
        if not client_name:
            return "Please provide your name to book the appointment."

        if not all([year, month, day]):
            return "Please provide the date for the appointment."

        if hour is None or minute is None:
            return "Please provide the time (30-minute slots only)."

        time = datetime.datetime(year, month, day, hour, minute)
        now = datetime.datetime.now()

        if time < now:
            return "You cannot book an appointment in the past."

        if minute not in [0, 30]:
            return "Appointments must be in 30-min slots."

        existing = db.query(Appointment).filter(Appointment.time == time).first()
        if existing:
            return f"Appointment at {time} is already booked"

        new_appointment = Appointment(client_name=client_name, time=time)
        db.add(new_appointment)
        db.commit()

        return f"Appointment successfully booked for {time}"

    finally:
        db.close()


# ---------------- CANCEL ----------------
@tool
def cancel_appointment(
    index: int = None,
    year: int = None,
    month: int = None,
    day: int = None,
    hour: int = None,
    minute: int = None
):
    """Cancel appointment by index OR datetime"""

    db = SessionLocal()
    try:
        appointments = db.query(Appointment).order_by(Appointment.time).all()

        if not appointments:
            return "There are no appointments to cancel."

        # Cancel by index
        if index is not None:
            if index < 1 or index > len(appointments):
                return "Invalid selection."

            appt = appointments[index - 1]
            db.delete(appt)
            db.commit()

            return f"Cancelled {appt.client_name} at {appt.time}"

        # If missing → show options
        if not all([year, month, day, hour, minute]):
            return "Please select which appointment to cancel:\n" + "\n".join(
                [f"{i+1}. {a.client_name} at {a.time}" for i, a in enumerate(appointments)]
            )

        # Cancel by datetime
        time = datetime.datetime(year, month, day, hour, minute)

        appt = db.query(Appointment).filter(Appointment.time == time).first()

        if not appt:
            return "No matching appointment found."

        db.delete(appt)
        db.commit()

        return f"Appointment at {time} cancelled"

    finally:
        db.close()


# ---------------- LIST ----------------
@tool
def list_appointments():
    """Displays all booked appointments."""

    db = SessionLocal()
    try:
        appointments = db.query(Appointment).order_by(Appointment.time).all()

        if not appointments:
            return "There are no appointments scheduled."

        return "\n".join([
            f"{i+1}. {a.client_name} at {a.time}"
            for i, a in enumerate(appointments)
        ])

    finally:
        db.close()