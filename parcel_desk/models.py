"""Data models for residents and parcels."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class Resident:
    """Represents a dormitory or condo resident."""

    room_number: str
    name: str

    def __str__(self) -> str:
        return f"{self.name} (Room {self.room_number})"


@dataclass
class Parcel:
    """Represents a parcel held at the desk."""

    tracking_code: str
    resident: Resident
    courier: str
    pickup_code: str
    arrived_at: datetime
    status: str = "pending"
    collected_at: datetime | None = None

    def is_overdue(self, now: datetime | None = None, overdue_days: int = 3) -> bool:
        """Return True if a pending parcel has stayed longer than overdue_days."""
        if self.status != "pending":
            return False
        current = now or datetime.now(timezone.utc)
        return (current - self.arrived_at) > timedelta(days=overdue_days)

    def __str__(self) -> str:
        return (
            f"[{self.tracking_code}] {self.resident} | "
            f"Courier: {self.courier} | Code: {self.pickup_code} | Status: {self.status}"
        )
