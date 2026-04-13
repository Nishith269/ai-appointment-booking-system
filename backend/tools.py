import datetime
import logging
from langchain_core.tools import tool
from database import SessionLocal
from models import Appointment

logger = logging.getLogger("appointment_app")

# ---------------- GET NEXT AVAILABLE ----------------
@tool
def get_next_appointment():
    """Returns the next available unbooked 30-minute slot."""
    db = SessionLocal()
    try:
        now = datetime.datetime.now()

        minutes = (30 - now.minute % 30) % 30
        if minutes == 0:
            minutes = 30

        next_slot = now + datetime.timedelta(minutes=minutes)
        next_slot = next_slot.replace(second=0, microsecond=0)

        while True:
            exists = db.query(Appointment).filter(Appointment.time == next_slot).first()
            if not exists:
                break
            next_slot += datetime.timedelta(minutes=30)

        logger.info(f"Next available slot: {next_slot}")
        return f"The next available appointment is at {next_slot}"

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

        time = datetime.datetime(year, month, day, hour, minute)
        now = datetime.datetime.now()

        if time < now:
            return "Cannot book past appointments."

        if minute not in [0, 30]:
            return "Only 30-minute slots allowed."

        existing = db.query(Appointment).filter(Appointment.time == time).first()
        if existing:
            return f"Slot {time} already booked."

        new_appointment = Appointment(client_name=client_name, time=time)
        db.add(new_appointment)
        db.commit()

        logger.info(f"Booked appointment for {client_name} at {time}")
        return f"Booked for {time}"

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

            db.delete(appt)
            db.commit()

            logger.info(f"Cancelled appointment ID {id}")
            return f"Cancelled {appt.time}"

        appointments = db.query(Appointment).order_by(Appointment.time).all()

        if index is not None:
            if index < 1 or index > len(appointments):
                return "Invalid selection."

            appt = appointments[index - 1]
            db.delete(appt)
            db.commit()

            return f"Cancelled {appt.time}"

        if all([year, month, day, hour, minute]):
            time = datetime.datetime(year, month, day, hour, minute)
            appt = db.query(Appointment).filter(Appointment.time == time).first()

            if not appt:
                return "No matching appointment."

            db.delete(appt)
            db.commit()

            return f"Cancelled {time}"

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
                "time": a.time.strftime("%Y-%m-%d %H:%M:%S")
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