from ..orchestrator import route
import traceback

def chat(agent, message):
    try:
        result = route(agent, message)
        return {"response": result}
    except Exception as e:
        print("/chat endpoint error:", e)
        traceback.print_exc()
        return {"error": str(e), "trace": traceback.format_exc()}
