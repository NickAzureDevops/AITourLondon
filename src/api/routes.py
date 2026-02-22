from fastapi import APIRouter, Request
from ..orchestrator import route
router = APIRouter()
from fastapi.responses import JSONResponse
import traceback

@router.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        agent = data.get("agent", "")
        message = data.get("message", "")
        result = route(agent, message)
        if hasattr(result, "__await__"):
            response = await result
        else:
            response = result
        return {"response": response}
    except Exception as e:
        print("/chat endpoint error:", e)
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})
