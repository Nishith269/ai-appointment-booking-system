from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
import datetime

from agent import caller_app
from langchain_core.messages import HumanMessage
from database import engine
from models import Base
from tools import cancel_appointment, book_appointment, list_appointments, get_next_appointment
from logger import setup_logger

logger = setup_logger()

Base.metadata.create_all(bind=engine)

app = FastAPI()

# -------- GLOBAL ERROR HANDLER --------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"message": "Internal Server Error"})


# -------- CHAT --------
class Query(BaseModel):
    message: str
    thread_id: str

@app.post("/chat")
def chat(query: Query):
    try:
        logger.info(f"Chat request: {query}")

        thread = {"configurable": {"thread_id": query.thread_id}}
        inputs = [HumanMessage(content=query.message)]

        response_text = ""

        for event in caller_app.stream({"messages": inputs}, thread, stream_mode="values"):
            response_text = event["messages"][-1].content

        return {"response": response_text}

    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat failed")


# -------- BOOK --------
class BookRequest(BaseModel):
    date: str
    time: str
    name: str
    email: EmailStr   

@app.post("/book")
def book(data: BookRequest):
    try:
        dt = datetime.datetime.strptime(f"{data.date} {data.time}", "%Y-%m-%d %H:%M:%S")

        response = book_appointment.invoke({
            "year": dt.year,
            "month": dt.month,
            "day": dt.day,
            "hour": dt.hour,
            "minute": dt.minute,
            "client_name": data.name,
            "email": data.email
        })

        return {"response": response}

    except Exception as e:
        logger.error(f"Book error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Booking failed")


# -------- CANCEL --------

class CancelRequest(BaseModel):
    id: int | None = None
    index: int | None = None
    date: str | None = None
    time: str | None = None


@app.post("/cancel")
def cancel(data: CancelRequest):
    try:
        if data.id is not None:
            return {"response": cancel_appointment.invoke({"id": data.id})}

        if data.index is not None:
            return {"response": cancel_appointment.invoke({"index": data.index})}

        if data.date and data.time:
            dt = datetime.datetime.strptime(f"{data.date} {data.time}", "%Y-%m-%d %H:%M:%S")

            return {"response": cancel_appointment.invoke({
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "hour": dt.hour,
                "minute": dt.minute
            })}

        raise HTTPException(status_code=400, detail="Invalid cancel request")

    except Exception as e:
        logger.error(f"Cancel error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Cancel failed")


# -------- LIST --------
@app.post("/list")
def list_all():
    try:
        data = list_appointments.invoke({})
        return {"appointments": data}
    except Exception as e:
        logger.error(f"List error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="List failed")

# -------- NEXT SLOT --------
@app.post("/next")
def next_slot():
    try:
        return {"response": get_next_appointment.invoke({})}
    except Exception as e:
        logger.error(f"Next slot error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Next slot failed")