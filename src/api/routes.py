from fastapi import APIRouter
from pydantic import BaseModel
from ..orchestrator import route
import traceback

router = APIRouter()

class ChatRequest(BaseModel):
    agent: str
    message: str

@router.post("/chat")
def chat(request: ChatRequest):
    try:
        result = route(request.agent, request.message)
        return {"response": result}
    except Exception as e:
        print("/chat endpoint error:", e)
        traceback.print_exc()
        return {"error": str(e), "trace": traceback.format_exc()}
