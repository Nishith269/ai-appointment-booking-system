import logging
from langchain_core.tools import tool
from database import SessionLocal
from models import Appointment

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

logger = logging.getLogger("appointment_app")

# ---------------- GET NEXT AVAILABLE ----------------
@tool
def get_next_appointment():
    """Returns the next available unbooked 30-minute slot."""
    db = SessionLocal()
    try:
        now = datetime.now(IST).replace(tzinfo=None)

        minutes = (30 - now.minute % 30) % 30
        if minutes == 0:
            minutes = 30

        next_slot = now + timedelta(minutes=minutes)
        next_slot = next_slot.replace(second=0, microsecond=0)

        while True:
            exists = db.query(Appointment).filter(Appointment.time == next_slot).first()
            if not exists:
                break
            next_slot += timedelta(minutes=30)

        formatted = next_slot.strftime("%d %b %Y, %I:%M %p IST")

        logger.info(f"Next available slot: {formatted}")
        return f"The next available appointment is at {formatted}"

    except Exception as e:
        logger.error(f"Error in get_next_appointment: {str(e)}", exc_info=True)
        return "Error fetching next available slot"

    finally:
        db.close()


# ---------------- BOOK ----------------
@tool
def book_appointment(year=None, month=None, day=None, hour=None, minute=None, client_name=None):
    """Books an appointment if the slot is available."""
    db = SessionLocal()
    try:
        if not client_name:
            return "Please provide your name."

        if not all([year, month, day]):
            return "Please provide the date."

        if hour is None or minute is None:
            return "Please provide time."


        time = datetime(year, month, day, hour, minute)
        now = datetime.now(IST).replace(tzinfo=None)

        if time < now:
            return "Cannot book past appointments."

        if minute not in [0, 30]:
            return "Only 30-minute slots allowed."

        existing = db.query(Appointment).filter(Appointment.time == time).first()
        if existing:
            formatted = time.strftime("%d %b %Y, %I:%M %p IST")
            return f"Slot {formatted} already booked."

        new_appointment = Appointment(client_name=client_name, time=time)
        db.add(new_appointment)
        db.commit()

        formatted = time.strftime("%d %b %Y, %I:%M %p IST")

        logger.info(f"Booked appointment for {client_name} at {formatted}")
        return f"Booked for {formatted}"

    except Exception as e:
        logger.error(f"Booking error: {str(e)}", exc_info=True)
        return "Error booking appointment"

    finally:
        db.close()


# ---------------- CANCEL ----------------
@tool
def cancel_appointment(id: int = None, index: int = None, year=None, month=None, day=None, hour=None, minute=None):
    """Cancels an appointment by id, index, or datetime."""
    db = SessionLocal()
    try:
        if id is not None:
            appt = db.query(Appointment).filter(Appointment.id == id).first()

            if not appt:
                return "Appointment not found."

            formatted = appt.time.strftime("%d %b %Y, %I:%M %p IST")
            db.delete(appt)
            db.commit()

            logger.info(f"Cancelled appointment ID {id}")
            return f"Cancelled {formatted}"

        appointments = db.query(Appointment).order_by(Appointment.time).all()

        if index is not None:
            if index < 1 or index > len(appointments):
                return "Invalid selection."

            appt = appointments[index - 1]
            formatted = appt.time.strftime("%d %b %Y, %I:%M %p IST")

            db.delete(appt)
            db.commit()

            return f"Cancelled {formatted}"

        if all([year, month, day, hour, minute]):
            time = datetime(year, month, day, hour, minute)
            appt = db.query(Appointment).filter(Appointment.time == time).first()

            if not appt:
                return "No matching appointment."

            formatted = time.strftime("%d %b %Y, %I:%M %p IST")

            db.delete(appt)
            db.commit()

            return f"Cancelled {formatted}"

        return "Provide id, index, or datetime"

    except Exception as e:
        logger.error(f"Cancel error: {str(e)}", exc_info=True)
        return "Error cancelling appointment"

    finally:
        db.close()


# ---------------- LIST ----------------
@tool
def list_appointments():
    """Returns all appointments in structured format."""
    db = SessionLocal()
    try:
        appointments = db.query(Appointment).order_by(Appointment.time).all()

        if not appointments:
            return []

        result = [
            {
                "id": a.id,
                "client_name": a.client_name,
                "time": a.time.strftime("%d %b %Y, %I:%M %p IST")
            }
            for a in appointments
        ]

        logger.info("Listed appointments (structured)")
        return result

    except Exception as e:
        logger.error(f"List error: {str(e)}", exc_info=True)
        return []

    finally:
        db.close()