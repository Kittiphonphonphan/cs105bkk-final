"""models.py: Parcel and Resident."""

from dataclasses import dataclass, field
from datetime import date

OVERDUE_DAYS = 7


@dataclass
class Parcel:
    parcel_no: str
    room: str
    recipient: str
    arrived_on: date
    code: str
    collected: bool = False

    @property
    def is_overdue(self) -> bool:
        if self.collected:
            return False
        days_waited = (date.today() - self.arrived_on).days
        return days_waited > OVERDUE_DAYS


@dataclass
class Resident:
    name: str
    room: str
    parcels: list[Parcel] = field(default_factory=list)

    def add_parcel(self, parcel: Parcel) -> None:
        self.parcels.append(parcel)

    def waiting(self) -> list[Parcel]:
        return [p for p in self.parcels if not p.collected]