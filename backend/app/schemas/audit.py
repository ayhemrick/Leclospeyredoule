"""Audit log schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.schemas.common import ApiModel


class AuditLogOut(ApiModel):
    """One entry of the admin activity log."""

    id: uuid.UUID
    action: str
    actor_admin_id: uuid.UUID | None
    actor_label: str
    entity_type: str | None
    entity_id: str | None
    context: dict[str, Any]
    created_at: datetime
