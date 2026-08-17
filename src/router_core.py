from fastapi import FastAPI
from src.db.init import init_db
from src.routers.chat import router as chat_router

app = FastAPI(title="LLM Router & Evaluator Proxy")


@app.on_event("startup")
def startup_event():
    init_db()


app.include_router(chat_router)
