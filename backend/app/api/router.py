"""Aggregate router for version 1 of the API."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    access,
    admin_access,
    admin_audit,
    admin_content,
    admin_users,
    auth,
    public,
)

api_router = APIRouter(prefix="/api/v1")

for module in (auth, access, public, admin_access, admin_content, admin_users, admin_audit):
    api_router.include_router(module.router)
