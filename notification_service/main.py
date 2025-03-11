from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
from typing import List, Dict
import json

app = FastAPI(title="Notification Service")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Subscribers for different notification channels
sse_subscribers: List[asyncio.Queue] = []
websocket_subscribers: List[WebSocket] = []
loan_status_updates: Dict[str, dict] = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_subscribers.append(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "subscribe" and message.get("loan_id"):
                    # Send current status if available
                    loan_id = message["loan_id"]
                    if loan_id in loan_status_updates:
                        await websocket.send_json(loan_status_updates[loan_id])
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        websocket_subscribers.remove(websocket)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )

@app.get("/sse")
async def sse_endpoint(request: Request):
    queue: asyncio.Queue = asyncio.Queue()
    sse_subscribers.append(queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await queue.get()
                if isinstance(message, dict):
                    yield f"data: {json.dumps(message)}\n\n"
                else:
                    yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            sse_subscribers.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

async def broadcast_websocket(message: dict):
    """Broadcast message to all connected WebSocket clients"""
    dead_connections = []
    for websocket in websocket_subscribers:
        try:
            await websocket.send_json(message)
        except RuntimeError:
            dead_connections.append(websocket)
    
    # Cleanup dead connections
    for dead in dead_connections:
        websocket_subscribers.remove(dead)

async def broadcast_sse(message: str):
    """Broadcast message to all SSE subscribers"""
    for queue in sse_subscribers:
        await queue.put(message)

async def broadcast_message(message: dict):
    """Broadcast message to all channels and update status"""
    # Update loan status if applicable
    if "loan_id" in message:
        loan_status_updates[message["loan_id"]] = message
    
    # Broadcast to all channels
    await asyncio.gather(
        broadcast_websocket(message),
        broadcast_sse(json.dumps(message))
    )
