from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

from fastapi import (
    Body,
    Depends,
    FastAPI,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import dispose_engine, get_session
from app.event_ingestion import (
    EventConflictError,
    InvalidOriginalSaleError,
    OriginalSaleNotFoundError,
    RefundLimitExceededError,
    RefundReferenceMismatchError,
    UnknownProductError,
    UnknownStoreError,
    ingest_refund_event,
    ingest_sale_event,
)
from app.models import Store
from app.realtime import manager
from app.schemas import (
    EventCreate,
    EventIngestResponse,
    HealthResponse,
    HeartbeatResponse,
    RefundEventCreate,
    StoreResponse,
)
from app.services import is_store_online

settings = get_settings()
SessionDep = Annotated[AsyncSession, Depends(get_session)]
EventBody = Annotated[EventCreate, Body(discriminator="event_type")]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await dispose_engine()


app = FastAPI(title=settings.project_name, version="0.3.0", lifespan=lifespan)
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


@app.post(
    "/api/v1/events",
    response_model=EventIngestResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_200_OK: {
            "model": EventIngestResponse,
            "description": "Exact duplicate; no second event was created",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Unknown store, product or original sale",
        },
        status.HTTP_409_CONFLICT: {
            "description": "event_id conflict or refund exceeds remaining sale",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Invalid event payload or refund reference",
        },
    },
)
async def create_event(
    payload: EventBody,
    response: Response,
    session: SessionDep,
) -> EventIngestResponse:
    try:
        if isinstance(payload, RefundEventCreate):
            result = await ingest_refund_event(session, payload)
        else:
            result = await ingest_sale_event(session, payload)
    except UnknownStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="unknown store",
        ) from exc
    except UnknownProductError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="unknown product",
        ) from exc
    except OriginalSaleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="original sale not found",
        ) from exc
    except InvalidOriginalSaleError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="original_event_id must reference a SALE",
        ) from exc
    except RefundReferenceMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except RefundLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except EventConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="event_id already exists with different payload",
        ) from exc

    if result.status == "duplicate":
        response.status_code = status.HTTP_200_OK
    else:
        await manager.broadcast({"type": "events.changed", "store_code": payload.store_code})

    return EventIngestResponse(
        event_id=result.event_id,
        status=result.status,
        received_at=result.received_at,
    )


@app.websocket("/ws/dashboard")
async def dashboard_socket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
