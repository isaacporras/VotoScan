from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .political_party import PoliticalParty
from .voter import Voter


class Assembly:
    """Assembly model containing only the list of deputies."""

    def __init__(self) -> None:
        self.deputies: list[Voter] = []

    def add_deputy(self, deputy: Voter) -> None:
        self.deputies.append(deputy)

    def get_seat_assignments(self) -> list[dict[str, Any]]:
        """Return assembly composition ordered by seat number."""
        assignments = sorted(self.deputies, key=lambda dep: (dep.seat_number or 10**9, dep.name))
        return [
            {
                "seat_number": deputy.seat_number,
                "name": deputy.name,
                "party": deputy.party.value,
            }
            for deputy in assignments
        ]

    def load_roster_from_json(self, json_path: str | Path) -> None:
        """Populate deputies from a JSON roster."""
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"roster file not found: {path}")

        data = json.loads(path.read_text(encoding="utf-8-sig"))
        deputies = data.get("deputies")
        if not isinstance(deputies, list):
            raise ValueError("JSON must contain a 'deputies' list")

        self.deputies.clear()
        for index, item in enumerate(deputies, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"deputies[{index}] must be an object")

            name = str(item.get("name", "")).strip()
            if not name:
                raise ValueError(f"deputies[{index}] is missing 'name'")

            raw_party = item.get("party")
            if not isinstance(raw_party, str) or not raw_party.strip():
                raise ValueError(f"deputies[{index}] is missing 'party'")

            raw_seat = item.get("seat_number", index)
            if not isinstance(raw_seat, int) or raw_seat < 1:
                raise ValueError(f"deputies[{index}] has invalid 'seat_number'")

            party = PoliticalParty.from_text(raw_party)
            self.add_deputy(Voter(name=name, party=party, seat_number=raw_seat))

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_deputies": len(self.deputies),
            "deputies": [deputy.to_dict() for deputy in self.deputies],
        }
