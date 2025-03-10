from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import asyncio
from typing import List

app = FastAPI(title="Notification Service")

# Liste globale de subscribers (queues asynchrones)
subscribers: List[asyncio.Queue] = []

@app.get("/", response_class=HTMLResponse)
def index():
    # Une page HTML minimale pour afficher les notifications
    return """
    <html>
      <head>
        <title>Notification Service</title>
      </head>
      <body>
        <h1>Notifications en temps réel</h1>
        <div id="events"></div>
        <script>
          const evtSource = new EventSource("/sse");
          evtSource.onmessage = function(event) {
            const newElement = document.createElement("div");
            newElement.textContent = event.data;
            document.getElementById("events").appendChild(newElement);
          };
        </script>
      </body>
    </html>
    """

@app.get("/sse")
async def sse_endpoint(request: Request):
    """
    Endpoint SSE pour envoyer des notifications en temps réel.
    Pour chaque client, on crée une queue asynchrone et on renvoie les messages au fur et à mesure.
    """
    queue: asyncio.Queue = asyncio.Queue()
    subscribers.append(queue)

    async def event_generator():
        try:
            while True:
                # Si la connexion se ferme, on interrompt
                if await request.is_disconnected():
                    break
                message = await queue.get()
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

def broadcast_message(message: str):
    """
    Diffuse un message à tous les clients connectés.
    """
    for queue in subscribers:
        queue.put_nowait(message)
