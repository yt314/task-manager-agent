import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent_service import agent

logger = logging.getLogger(__name__)

app = FastAPI(title="Task Manager Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        answer = agent(request.message)
        return ChatResponse(response=answer)
    except Exception:
        logger.exception("Unhandled error while processing request")
        return JSONResponse(
            status_code=500,
            content={"error": "אירעה שגיאה בעיבוד הבקשה. נסי שוב בעוד רגע."},
        )


class ForceCORSHeaders:
    """
    Guarantees Access-Control-Allow-Origin is present on every response,
    including ones from crashes that bypass CORSMiddleware entirely
    (Starlette's ServerErrorMiddleware sits outside it and never calls it).
    """

    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.asgi_app(scope, receive, send)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                if not any(h[0] == b"access-control-allow-origin" for h in headers):
                    headers.append((b"access-control-allow-origin", b"*"))
                message["headers"] = headers
            await send(message)

        await self.asgi_app(scope, receive, send_wrapper)


app = ForceCORSHeaders(app)
