"""Command-line interface for the Parcel Desk application."""

from __future__ import annotations

from pathlib import Path

from parcel_desk.manager import ParcelDesk, ParcelError
from parcel_desk.storage import ParcelStorage, StorageError

DEFAULT_DATA_FILE = Path("data/parcels.json")


def _print_menu() -> None:
    """Display main menu options."""
    print("\n=== Parcel Desk CLI ===")
    print("1. Receive parcel")
    print("2. Find parcels by room")
    print("3. Collect parcel")
    print("4. View overdue parcels")
    print("5. List all pending parcels")
    print("0. Exit")


def _handle_receive(desk: ParcelDesk) -> None:
    """Prompt user to register a new parcel."""
    tracking = input("Tracking code: ")
    room = input("Room number: ")
    name = input("Recipient name: ")
    courier = input("Courier (default: General): ")

    parcel = desk.receive_parcel(
        tracking_code=tracking,
        room_number=room,
        resident_name=name,
        courier=courier,
    )
    print(f"Saved! Pickup code for {parcel.tracking_code}: {parcel.pickup_code}")


def _handle_find_by_room(desk: ParcelDesk) -> None:
    """Prompt user for room number and display matching pending parcels."""
    room = input("Room number: ")
    matches = desk.find_by_room(room, only_pending=True)
    if not matches:
        print("No pending parcels found for that room.")
        return
    for parcel in matches:
        print(f"- {parcel}")


def _handle_collect(desk: ParcelDesk) -> None:
    """Prompt user to collect a parcel using tracking and pickup codes."""
    tracking = input("Tracking code: ")
    code = input("Pickup code: ")
    parcel = desk.collect_parcel(tracking_code=tracking, pickup_code=code)
    print(f"Collected parcel {parcel.tracking_code} for room {parcel.resident.room_number}.")


def _handle_overdue(desk: ParcelDesk) -> None:
    """Display parcels past the overdue threshold."""
    overdue_items = desk.list_overdue_parcels()
    if not overdue_items:
        print(f"No overdue parcels (threshold: {desk.overdue_days} days).")
        return
    print(f"Overdue parcels (> {desk.overdue_days} days):")
    for parcel in overdue_items:
        print(f"- {parcel}")


def _handle_pending(desk: ParcelDesk) -> None:
    """Display all currently pending parcels."""
    pending = [p for p in desk.parcels if p.status == "pending"]
    if not pending:
        print("No pending parcels.")
        return
    for parcel in pending:
        print(f"- {parcel}")


def run_cli(data_path: Path = DEFAULT_DATA_FILE) -> None:
    """Start the interactive CLI loop."""
    try:
        storage = ParcelStorage(data_path)
        desk = ParcelDesk(storage=storage, overdue_days=3)
    except (StorageError, ValueError, OSError) as exc:
        print(f"Startup error: {exc}")
        return

    actions = {
        "1": _handle_receive,
        "2": _handle_find_by_room,
        "3": _handle_collect,
        "4": _handle_overdue,
        "5": _handle_pending,
    }

    while True:
        _print_menu()
        try:
            choice = input("Choose an option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Parcel Desk.")
            break

        if choice == "0":
            print("Goodbye!")
            break

        handler = actions.get(choice)
        if handler is None:
            print("Invalid option. Please choose from the menu.")
            continue

        try:
            handler(desk)
        except ParcelError as exc:
            print(f"Action failed: {exc}")
        except (EOFError, KeyboardInterrupt):
            print("\nInput cancelled.")
        except Exception as exc:  # noqa: BLE001 - guard CLI against unexpected crashes
            print(f"Unexpected error: {exc}")
