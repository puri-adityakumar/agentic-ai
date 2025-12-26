import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.db import init_db
from api.chat.routing import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # before app startup
    init_db()
    yield
    # after app startup

app = FastAPI(lifespan=lifespan)
app.include_router(chat_router, prefix="/api/chats")

MY_PROJECT = os.environ.get("MY_PROJECT") or "This is my project"
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise NotImplementedError("'API_KEY' was not set")

@app.get("/")
def read_index():
    return {"hello": "worlded!", "project_name": MY_PROJECT}


@app.get("/health")
def heath_check():
    return {"status": "ok"}