"""ORM models.

Importing this package registers every table on :class:`app.db.base.Base`,
which is what Alembic autogenerate and the test fixtures rely on.
"""

from app.models.access import (
    POLICY_SINGLETON_ID,
    AccessCode,
    AccessPolicy,
    GuestSession,
    RotationReason,
)
from app.models.admin_user import AdminRole, AdminUser
from app.models.audit_log import AuditLog
from app.models.content import (
    Attraction,
    AttractionCategory,
    GuideCategory,
    GuideSection,
    Visibility,
)

__all__ = [
    "POLICY_SINGLETON_ID",
    "AccessCode",
    "AccessPolicy",
    "AdminRole",
    "AdminUser",
    "Attraction",
    "AttractionCategory",
    "AuditLog",
    "GuestSession",
    "GuideCategory",
    "GuideSection",
    "RotationReason",
    "Visibility",
]
