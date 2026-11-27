"""JSON persistence layer using pathlib."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from parcel_desk.models import Parcel, Resident


class StorageError(Exception):
    """Raised when loading or saving parcel data fails."""


class ParcelStorage:
    """Reads and writes parcels to a JSON file."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = Path(file_path)

    def load_parcels(self) -> list[Parcel]:
        """Load parcels from JSON; return an empty list if the file does not exist."""
        if not self.file_path.exists():
            return []

        try:
            raw_text = self.file_path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"Failed to read '{self.file_path}': {exc}") from exc

        if not isinstance(data, list):
            raise StorageError("Parcel data file must contain a JSON list.")

        parcels: list[Parcel] = []
        for item in data:
            try:
                resident_data = item["resident"]
                resident = Resident(
                    room_number=str(resident_data["room_number"]),
                    name=str(resident_data["name"]),
                )
                collected_raw = item.get("collected_at")
                collected_at = (
                    datetime.fromisoformat(collected_raw)
                    if collected_raw is not None
                    else None
                )
                parcel = Parcel(
                    tracking_code=str(item["tracking_code"]),
                    resident=resident,
                    courier=str(item.get("courier", "General")),
                    pickup_code=str(item["pickup_code"]),
                    arrived_at=datetime.fromisoformat(item["arrived_at"]),
                    status=str(item.get("status", "pending")),
                    collected_at=collected_at,
                )
                parcels.append(parcel)
            except (KeyError, TypeError, ValueError) as exc:
                raise StorageError(f"Invalid parcel record in '{self.file_path}': {exc}") from exc

        return parcels

    def save_parcels(self, parcels: list[Parcel]) -> None:
        """Save all parcels to JSON."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            payload = [
                {
                    "tracking_code": p.tracking_code,
                    "resident": {
                        "room_number": p.resident.room_number,
                        "name": p.resident.name,
                    },
                    "courier": p.courier,
                    "pickup_code": p.pickup_code,
                    "arrived_at": p.arrived_at.isoformat(),
                    "status": p.status,
                    "collected_at": p.collected_at.isoformat() if p.collected_at else None,
                }
                for p in parcels
            ]
            self.file_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise StorageError(f"Failed to write '{self.file_path}': {exc}") from exc
