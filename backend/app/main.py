from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import dispose_engine, get_session
from app.models import Store
from app.realtime import manager
from app.schemas import HealthResponse, HeartbeatResponse, StoreResponse
from app.services import is_store_online

settings = get_settings()
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await dispose_engine()


app = FastAPI(title=settings.project_name, version="0.1.3", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/v1/health/live", response_model=HealthResponse)
async def health_live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/api/v1/health/ready", response_model=HealthResponse)
async def health_ready(session: SessionDep) -> HealthResponse:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from exc
    return HealthResponse(status="ready")


@app.get("/api/v1/stores", response_model=list[StoreResponse])
async def list_stores(session: SessionDep) -> list[StoreResponse]:
    query = select(Store).where(Store.is_active.is_(True)).order_by(Store.name)
    result = await session.execute(query)
    stores = result.scalars().all()
    now = datetime.now(UTC)
    return [
        StoreResponse(
            id=store.id,
            name=store.name,
            code=store.code,
            timezone=store.timezone,
            daily_target_cents=store.daily_target_cents,
            responsible_name=store.responsible_name,
            responsible_email=store.responsible_email,
            last_seen_at=store.last_seen_at,
            online=is_store_online(
                store.last_seen_at,
                now=now,
                threshold_seconds=settings.offline_threshold_seconds,
            ),
        )
        for store in stores
    ]


@app.post("/api/v1/stores/{store_code}/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(store_code: str, session: SessionDep) -> HeartbeatResponse:
    result = await session.execute(select(Store).where(Store.code == store_code))
    store = result.scalar_one_or_none()
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown store")

    now = datetime.now(UTC)
    store.last_seen_at = now
    await session.commit()
    await manager.broadcast({"type": "stores.changed", "store_code": store.code})

    return HeartbeatResponse(store_code=store.code, last_seen_at=now, status="accepted")


@app.websocket("/ws/dashboard")
async def dashboard_socket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
