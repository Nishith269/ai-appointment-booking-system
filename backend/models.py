from sqlalchemy import Column, Integer, String, DateTime
from database import Base

# All times are stored as naive IST (no timezone)

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True) 
    time = Column(DateTime, nullable=False)
