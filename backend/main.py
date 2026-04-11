from fastapi import FastAPI
from pydantic import BaseModel
from agent import caller_app
from langchain_core.messages import HumanMessage

app = FastAPI()

class Query(BaseModel):
    message: str
    thread_id: str = "1"

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