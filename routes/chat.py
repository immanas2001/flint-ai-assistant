from fastapi import APIRouter
from pydantic import BaseModel

from assistant.ai import ask_ai
from assistant.memory import clear_history

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(data: ChatRequest):

    reply = ask_ai(data.message)

    return {
        "reply": reply
    }


@router.post("/new-chat")
async def new_chat():

    clear_history()

    return {
        "status": "success"
    }