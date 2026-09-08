from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str


class StoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    timezone: str
    daily_target_cents: int
    responsible_name: str
    responsible_email: str
    last_seen_at: datetime | None
    online: bool


class HeartbeatResponse(BaseModel):
    store_code: str
    last_seen_at: datetime
    status: str


class SaleEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: UUID
    store_code: str = Field(min_length=1, max_length=40)
    product_sku: str = Field(min_length=1, max_length=64)
    event_type: Literal["SALE"]
    quantity: int = Field(gt=0, strict=True)
    amount_cents: int = Field(gt=0, strict=True)
    occurred_at: AwareDatetime
    source_instance: str = Field(min_length=1, max_length=120)
    metadata: dict[str, object] | None = None
    note: str | None = None


class EventIngestResponse(BaseModel):
    event_id: UUID
    status: Literal["accepted", "duplicate"]
    received_at: datetime
