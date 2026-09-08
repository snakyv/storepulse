from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
