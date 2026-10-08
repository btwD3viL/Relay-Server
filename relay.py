import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from contextlib import asynccontextmanager

TUNNEL_URL = os.getenv("TUNNEL_URL")
_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    if not TUNNEL_URL:
        raise RuntimeError("TUNNEL_URL not set")
    _client = httpx.AsyncClient(timeout=30.0)
    yield
    await _client.aclose()


app = FastAPI(lifespan=lifespan)


@app.post("/your/endpoint")
async def forward(request: Request):
    global _client
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty body")

    headers = {"Content-Type": "application/json"}
    try:
        resp = await _client.post(f"{TUNNEL_URL}/your/endpoint", content=body, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")

    return Response(content=resp.content, status_code=resp.status_code,
                    media_type=resp.headers.get("content-type", "application/json"))