from fastapi import FastAPI
from .api.routes import router

app = FastAPI()
app.include_router(router)

@app.get("/")
def root():
    return {"message": "AI Tour Concierge backend is running."}
