import json
from datetime import date
from pathlib import Path

from models import Parcel

class ParcelStorage:
    def __init__(self, path: Path):
        self.path = path

    def save(self, parcels: list[Parcel]) -> None:
        data = [
            {
                "parcel_no": p.parcel_no,
                "room": p.room,
                "recipient": p.recipient,
                "arrived_on": p.arrived_on.isoformat(),
                "code": p.code,
                "collected": p.collected,
            }
            for p in parcels
        ]
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def load(self) -> list[Parcel]:
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        return [
            Parcel(
                parcel_no=d["parcel_no"],
                room=d["room"],
                recipient=d["recipient"],
                arrived_on=date.fromisoformat(d["arrived_on"]),
                code=d["code"],
                collected=d["collected"],
            )
            for d in data
        ]