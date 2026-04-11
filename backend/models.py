from pydantic import BaseModel

class AskHuman(BaseModel):
    """Ask the human a question"""
    question: str