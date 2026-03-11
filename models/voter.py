from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .political_party import PoliticalParty


@dataclass(frozen=True)
class Voter:
    """A deputy (voter) with name and political party."""

    name: str
    party: PoliticalParty
    seat_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "party": self.party.value,
            "seat_number": self.seat_number,
        }
