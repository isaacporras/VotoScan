from __future__ import annotations

from enum import Enum
import unicodedata


class PoliticalParty(Enum):
    """Political parties represented in this project."""

    PLN = "Partido Liberacion Nacional (PLN)"
    PPSD = "Partido Progreso Social Democratico (PPSD)"
    PUSC = "Partido Unidad Social Cristiana (PUSC)"
    NUEVA_REPUBLICA = "Partido Nueva Republica"
    FRENTE_AMPLIO = "Frente Amplio"
    PLP = "Partido Liberal Progresista (PLP)"
    INDEPENDENT = "Independent"

    @classmethod
    def from_text(cls, raw: str) -> PoliticalParty:
        """Resolve a party from enum key, acronym or full display name."""
        normalized = cls._normalize_text(raw)
        alias_map = {
            "pln": cls.PLN,
            "ppsd": cls.PPSD,
            "pusc": cls.PUSC,
            "nueva_republica": cls.NUEVA_REPUBLICA,
            "nueva republica": cls.NUEVA_REPUBLICA,
            "frente_amplio": cls.FRENTE_AMPLIO,
            "frente amplio": cls.FRENTE_AMPLIO,
            "plp": cls.PLP,
            "independent": cls.INDEPENDENT,
            "independiente": cls.INDEPENDENT,
            "ind": cls.INDEPENDENT,
        }
        if normalized in alias_map:
            return alias_map[normalized]

        for member in cls:
            if normalized == cls._normalize_text(member.name) or normalized == cls._normalize_text(member.value):
                return member

        raise ValueError(f"unknown political party: {raw}")

    @staticmethod
    def _normalize_text(value: str) -> str:
        base = unicodedata.normalize("NFKD", value.strip().lower())
        return "".join(ch for ch in base if not unicodedata.combining(ch))
