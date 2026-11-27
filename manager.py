"""Core business logic for managing dormitory or condo parcels."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
import random
import string

from parcel_desk.models import Parcel, Resident
from parcel_desk.storage import ParcelStorage


class ParcelError(Exception):
    """Raised when a parcel operation cannot be completed."""


class ParcelDesk:
    """Manages incoming parcels, pickups, searches, and overdue tracking."""

    def __init__(self, storage: ParcelStorage, overdue_days: int = 3) -> None:
        if overdue_days < 1:
            raise ValueError("overdue_days must be at least 1.")
        self.storage = storage
        self.overdue_days = overdue_days
        self.parcels: list[Parcel] = self.storage.load_parcels()

    def _generate_pickup_code(self, length: int = 4) -> str:
        """Generate a unique numeric pickup code for active parcels."""
        existing_codes = {
            p.pickup_code for p in self.parcels if p.status == "pending"
        }
        for _ in range(100):
            code = "".join(random.choices(string.digits, k=length))
            if code not in existing_codes:
                return code
        raise ParcelError("Unable to generate a unique pickup code.")

    def receive_parcel(
        self,
        tracking_code: str,
        room_number: str,
        resident_name: str,
        courier: str = "General",
    ) -> Parcel:
        """Register a new incoming parcel and save immediately."""
        clean_tracking = tracking_code.strip().upper()
        clean_room = room_number.strip().upper()
        clean_name = resident_name.strip()
        clean_courier = courier.strip() or "General"

        if not clean_tracking or not clean_room or not clean_name:
            raise ParcelError("Tracking code, room number, and recipient name are required.")

        if any(p.tracking_code == clean_tracking for p in self.parcels):
            raise ParcelError(f"Tracking code '{clean_tracking}' already exists.")

        resident = Resident(room_number=clean_room, name=clean_name)
        parcel = Parcel(
            tracking_code=clean_tracking,
            resident=resident,
            courier=clean_courier,
            pickup_code=self._generate_pickup_code(),
            arrived_at=datetime.now(timezone.utc),
            status="pending",
        )
        self.parcels.append(parcel)
        self.storage.save_parcels(self.parcels)
        return parcel

    def find_by_room(self, room_number: str, only_pending: bool = True) -> list[Parcel]:
        """Return parcels matching a room number."""
        clean_room = room_number.strip().upper()
        if not clean_room:
            return []
        return [
            p
            for p in self.parcels
            if p.resident.room_number == clean_room
            and (not only_pending or p.status == "pending")
        ]

    def collect_parcel(self, tracking_code: str, pickup_code: str) -> Parcel:
        """Mark a pending parcel as collected when the pickup code matches."""
        clean_tracking = tracking_code.strip().upper()
        clean_code = pickup_code.strip()

        target = next((p for p in self.parcels if p.tracking_code == clean_tracking), None)
        if target is None:
            raise ParcelError(f"Parcel '{clean_tracking}' not found.")
        if target.status == "collected":
            raise ParcelError(f"Parcel '{clean_tracking}' has already been collected.")
        if target.pickup_code != clean_code:
            raise ParcelError("Invalid pickup code.")

        target.status = "collected"
        target.collected_at = datetime.now(timezone.utc)
        self.storage.save_parcels(self.parcels)
        return target

    def iter_overdue_parcels(
        self, reference_time: datetime | None = None
    ) -> Iterator[Parcel]:
        """Yield pending parcels that have stayed longer than overdue_days."""
        now = reference_time or datetime.now(timezone.utc)
        for parcel in self.parcels:
            if parcel.is_overdue(now=now, overdue_days=self.overdue_days):
                yield parcel

    def list_overdue_parcels(
        self, reference_time: datetime | None = None
    ) -> list[Parcel]:
        """Return overdue parcels as a list."""
        return list(self.iter_overdue_parcels(reference_time=reference_time))
