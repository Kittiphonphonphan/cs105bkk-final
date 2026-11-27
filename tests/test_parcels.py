from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from parcel_desk.manager import ParcelDesk, ParcelError
from parcel_desk.models import Parcel, Resident
from parcel_desk.storage import ParcelStorage, StorageError


def _make_desk(tmp_path: Path, overdue_days: int = 3) -> ParcelDesk:
    return ParcelDesk(
        storage=ParcelStorage(tmp_path / "parcels.json"),
        overdue_days=overdue_days,
    )


def test_receive_and_persist_parcel(tmp_path: Path) -> None:
    desk = _make_desk(tmp_path)
    parcel = desk.receive_parcel("th12345", "a402", "Nicha", "Flash")
    assert parcel.tracking_code == "TH12345"
    assert parcel.resident.room_number == "A402"
    assert len(parcel.pickup_code) == 4
    assert parcel.status == "pending"

    reloaded = _make_desk(tmp_path)
    assert len(reloaded.parcels) == 1


def test_collect_parcel_success(tmp_path: Path) -> None:
    desk = _make_desk(tmp_path)
    parcel = desk.receive_parcel("PKG001", "B101", "Ken")
    collected = desk.collect_parcel("pkg001", parcel.pickup_code)
    assert collected.status == "collected"
    assert desk.find_by_room("B101", only_pending=True) == []


def test_collect_parcel_wrong_code_raises(tmp_path: Path) -> None:
    desk = _make_desk(tmp_path)
    desk.receive_parcel("PKG002", "B102", "Mew")
    with pytest.raises(ParcelError, match="Invalid pickup code"):
        desk.collect_parcel("PKG002", "0000")


def test_collect_already_collected_raises(tmp_path: Path) -> None:
    desk = _make_desk(tmp_path)
    parcel = desk.receive_parcel("PKG003", "B103", "Ploy")
    desk.collect_parcel("PKG003", parcel.pickup_code)
    with pytest.raises(ParcelError, match="already been collected"):
        desk.collect_parcel("PKG003", parcel.pickup_code)


def test_duplicate_tracking_code_rejected(tmp_path: Path) -> None:
    desk = _make_desk(tmp_path)
    desk.receive_parcel("DUP100", "C201", "Sun")
    with pytest.raises(ParcelError, match="already exists"):
        desk.receive_parcel("dup100", "C202", "Win")


@pytest.mark.parametrize(
    ("tracking", "room", "name"),
    [
        ("", "A101", "Alice"),
        ("TRK1", "   ", "Bob"),
        ("TRK2", "A102", ""),
    ],
)
def test_receive_parcel_blank_fields_rejected(
    tmp_path: Path, tracking: str, room: str, name: str
) -> None:
    desk = _make_desk(tmp_path)
    with pytest.raises(ParcelError):
        desk.receive_parcel(tracking, room, name)


def test_overdue_boundary_exact_vs_exceeded(tmp_path: Path) -> None:
    desk = _make_desk(tmp_path, overdue_days=3)
    base_time = datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc)
    exact_parcel = Parcel(
        tracking_code="EXACT3",
        resident=Resident(room_number="D101", name="Exact"),
        courier="Kerry",
        pickup_code="1111",
        arrived_at=base_time,
    )
    overdue_parcel = Parcel(
        tracking_code="LATE4",
        resident=Resident(room_number="D102", name="Late"),
        courier="Kerry",
        pickup_code="2222",
        arrived_at=base_time - timedelta(seconds=1),
    )
    desk.parcels.extend([exact_parcel, overdue_parcel])
    overdue = desk.list_overdue_parcels(reference_time=base_time + timedelta(days=3))
    assert [p.tracking_code for p in overdue] == ["LATE4"]


def test_find_by_room_unknown_returns_empty(tmp_path: Path) -> None:
    desk = _make_desk(tmp_path)
    assert desk.find_by_room("Z999") == []


def test_missing_json_file_starts_clean(tmp_path: Path) -> None:
    storage = ParcelStorage(tmp_path / "nonexistent" / "parcels.json")
    assert storage.load_parcels() == []


def test_corrupted_json_file_raises_storage_error(tmp_path: Path) -> None:
    bad_file = tmp_path / "broken.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    storage = ParcelStorage(bad_file)
    with pytest.raises(StorageError):
        storage.load_parcels()

