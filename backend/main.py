from fastapi import FastAPI
from pydantic import BaseModel
from agent import caller_app
from langchain_core.messages import HumanMessage
from database import engine
from models import Base
from tools import cancel_appointment, book_appointment, list_appointments, get_next_appointment
import datetime
from tools import get_next_appointment


Base.metadata.create_all(bind=engine)

app = FastAPI()


# ---------------- CHAT ----------------
class Query(BaseModel):
    message: str
    thread_id: str


@app.post("/chat")
def chat(query: Query):
    thread = {"configurable": {"thread_id": query.thread_id}}

    inputs = [HumanMessage(content=query.message)]

    response_text = ""

    for event in caller_app.stream(
        {"messages": inputs}, thread, stream_mode="values"
    ):
        response_text = event["messages"][-1].content

    return {"response": response_text}


# ---------------- BOOK ----------------
class BookRequest(BaseModel):
    date: str
    time: str
    name: str


@app.post("/book")
def book(data: BookRequest):
    dt = datetime.datetime.strptime(
        f"{data.date} {data.time}",
        "%Y-%m-%d %H:%M:%S"
    )

    return {
        "response": book_appointment.invoke({
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "hour": dt.hour,
            "minute": dt.minute,
            "client_name": data.name
        })
    }


# ---------------- CANCEL ----------------
class CancelRequest(BaseModel):
    date: str
    time: str


@app.post("/cancel")
def cancel(data: CancelRequest):
    dt = datetime.datetime.strptime(
        f"{data.date} {data.time}",
        "%Y-%m-%d %H:%M:%S"
    )

    return {
        "response": cancel_appointment.invoke({
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "hour": dt.hour,
            "minute": dt.minute
        })
    }


# ---------------- LIST ----------------
@app.post("/list")
def list_all():
    return {
        "response": list_appointments.invoke({})
    }


# ---------------- NEXT AVAILABLE SLOT ----------------
@app.post("/next")
def next_slot():
    return {
        "response": get_next_appointment.invoke({})
    }