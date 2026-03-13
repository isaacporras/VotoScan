from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .political_party import PoliticalParty


@dataclass(frozen=True)
class Voter:
    """A deputy (voter) with structured names and political party."""

    given_names: str
    surnames: str
    party: PoliticalParty
    seat_number: int | None = None

    def __init__(
        self,
        *,
        party: PoliticalParty,
        seat_number: int | None = None,
        name: str | None = None,
        given_names: str | None = None,
        surnames: str | None = None,
    ) -> None:
        resolved_given_names, resolved_surnames = self._resolve_name_parts(
            name=name,
            given_names=given_names,
            surnames=surnames,
        )
        object.__setattr__(self, "given_names", resolved_given_names)
        object.__setattr__(self, "surnames", resolved_surnames)
        object.__setattr__(self, "party", party)
        object.__setattr__(self, "seat_number", seat_number)

    @property
    def name(self) -> str:
        return f"{self.given_names} {self.surnames}".strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "given_names": self.given_names,
            "surnames": self.surnames,
            "party": self.party.value,
            "seat_number": self.seat_number,
        }

    @staticmethod
    def _resolve_name_parts(
        *,
        name: str | None,
        given_names: str | None,
        surnames: str | None,
    ) -> tuple[str, str]:
        if given_names is not None or surnames is not None:
            resolved_given_names = str(given_names or "").strip()
            resolved_surnames = str(surnames or "").strip()
            if not resolved_given_names or not resolved_surnames:
                raise ValueError("voter requires both given_names and surnames")
            return resolved_given_names, resolved_surnames

        normalized_name = str(name or "").strip()
        if not normalized_name:
            raise ValueError("voter requires a name or structured name parts")

        parts = [part for part in normalized_name.split() if part]
        if len(parts) < 2:
            raise ValueError("voter name must include given names and surnames")
        if len(parts) == 2:
            return parts[0], parts[1]

        return " ".join(parts[:-2]), " ".join(parts[-2:])
