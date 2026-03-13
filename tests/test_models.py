import json
import unittest
from pathlib import Path
from uuid import uuid4

from models import Assembly, PoliticalParty, VoteChoice, Voter, VotingSession


class AssemblyLoadRosterTests(unittest.TestCase):
    def _write_temp_roster(self, payload: dict) -> Path:
        temp_dir = Path("tests/.tmp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        roster_path = temp_dir / f"deputies_{uuid4().hex}.json"
        roster_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return roster_path

    def test_load_roster_creates_voter_instances(self) -> None:
        roster_path = self._write_temp_roster(
            {
                "deputies": [
                    {"given_names": "Ana", "surnames": "Perez", "party": "PLN"},
                    {"given_names": "Luis", "surnames": "Mora", "party": "Frente Amplio"},
                    {"given_names": "Sam", "surnames": "Vega", "party": "ind"},
                ]
            }
        )

        assembly = Assembly()
        assembly.load_roster_from_json(roster_path)

        self.assertEqual(3, len(assembly.deputies))
        self.assertTrue(all(isinstance(dep, Voter) for dep in assembly.deputies))
        self.assertEqual(PoliticalParty.PLN, assembly.deputies[0].party)
        self.assertEqual(PoliticalParty.FRENTE_AMPLIO, assembly.deputies[1].party)
        self.assertEqual(PoliticalParty.INDEPENDENT, assembly.deputies[2].party)
        self.assertEqual("Ana", assembly.deputies[0].given_names)
        self.assertEqual("Perez", assembly.deputies[0].surnames)
        self.assertEqual(1, assembly.deputies[0].seat_number)
        self.assertEqual(2, assembly.deputies[1].seat_number)
        self.assertEqual(3, assembly.deputies[2].seat_number)

    def test_load_roster_supports_accented_party_name(self) -> None:
        roster_path = self._write_temp_roster(
            {
                "deputies": [
                    {"given_names": "Fabricio", "surnames": "Alvarado", "party": "Nueva República"},
                ]
            }
        )

        assembly = Assembly()
        assembly.load_roster_from_json(roster_path)

        self.assertEqual(PoliticalParty.NUEVA_REPUBLICA, assembly.deputies[0].party)

    def test_load_roster_raises_for_missing_deputies_list(self) -> None:
        roster_path = self._write_temp_roster({"items": []})

        assembly = Assembly()
        with self.assertRaises(ValueError):
            assembly.load_roster_from_json(roster_path)

    def test_load_roster_raises_for_unknown_party(self) -> None:
        roster_path = self._write_temp_roster(
            {
                "deputies": [
                    {"given_names": "Ana", "surnames": "Perez", "party": "UNKNOWN"},
                ]
            }
        )

        assembly = Assembly()
        with self.assertRaises(ValueError):
            assembly.load_roster_from_json(roster_path)

    def test_load_roster_raises_for_invalid_seat_number(self) -> None:
        roster_path = self._write_temp_roster(
            {
                "deputies": [
                    {"given_names": "Ana", "surnames": "Perez", "party": "PLN", "seat_number": 0},
                ]
            }
        )

        assembly = Assembly()
        with self.assertRaises(ValueError):
            assembly.load_roster_from_json(roster_path)

    def test_get_seat_assignments_returns_sorted_seats(self) -> None:
        assembly = Assembly()
        assembly.add_deputy(Voter(name="Deputy B", party=PoliticalParty.PUSC, seat_number=2))
        assembly.add_deputy(Voter(name="Deputy A", party=PoliticalParty.PLN, seat_number=1))

        assignments = assembly.get_seat_assignments()

        self.assertEqual(1, assignments[0]["seat_number"])
        self.assertEqual("Deputy A", assignments[0]["name"])
        self.assertEqual(2, assignments[1]["seat_number"])
        self.assertEqual("Deputy B", assignments[1]["name"])


if __name__ == "__main__":
    unittest.main()


class _FakeExtractor:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def extract_results(self, _path: str) -> dict:
        return self.payload


class VotingSessionProcessResultsTests(unittest.TestCase):
    def test_process_results_maps_ocr_names_to_deputies(self) -> None:
        deputies = [
            Voter(name="Leslye Bojorges León", party=PoliticalParty.PUSC),
            Voter(name="Daniela Rojas Salas", party=PoliticalParty.PPSD),
            Voter(name="Jonathan Acuña Soto", party=PoliticalParty.FRENTE_AMPLIO),
        ]
        session = VotingSession(name="mocion123", png_path="file.png", deputies=deputies)
        extractor = _FakeExtractor(
            {
                "a_favor": ["Bojorges Leén Leslye"],
                "en_contra": ["Rojas Salas, Daniela"],
                "no_votacion": ["Acuña Soto, Jonathan"],
            }
        )

        unmatched = session.process_results(extractor=extractor)

        self.assertEqual([], unmatched["a_favor"])
        self.assertEqual([], unmatched["en_contra"])
        self.assertEqual([], unmatched["no_votacion"])
        self.assertEqual(VoteChoice.IN_FAVOR, session.get_vote(deputies[0]))
        self.assertEqual(VoteChoice.AGAINST, session.get_vote(deputies[1]))
        self.assertEqual(VoteChoice.ABSTENTION, session.get_vote(deputies[2]))

    def test_process_results_tracks_unmatched_names(self) -> None:
        deputies = [Voter(name="Leslye Bojorges León", party=PoliticalParty.PUSC)]
        session = VotingSession(name="mocion123", png_path="file.png", deputies=deputies)
        extractor = _FakeExtractor(
            {
                "a_favor": ["Nombre Inexistente"],
                "en_contra": [],
                "no_votacion": [],
            }
        )

        unmatched = session.process_results(extractor=extractor)

        self.assertEqual(["Nombre Inexistente"], unmatched["a_favor"])
        self.assertEqual(VoteChoice.ABSENT, session.get_vote(deputies[0]))

    def test_process_results_matches_surnames_when_ocr_omits_given_names(self) -> None:
        deputies = [
            Voter(given_names="Kattia", surnames="Cambronero Aguiluz", party=PoliticalParty.PLP),
            Voter(given_names="Kattia", surnames="Rivera Soto", party=PoliticalParty.PLN),
        ]
        session = VotingSession(name="mocion123", png_path="file.png", deputies=deputies)
        extractor = _FakeExtractor(
            {
                "a_favor": ["Cambronero Aguiluz"],
                "en_contra": [],
                "no_votacion": [],
            }
        )

        unmatched = session.process_results(extractor=extractor)

        self.assertEqual([], unmatched["a_favor"])
        self.assertEqual(VoteChoice.IN_FAVOR, session.get_vote(deputies[0]))
        self.assertEqual(VoteChoice.ABSENT, session.get_vote(deputies[1]))

    def test_process_results_matches_multiple_deputies_from_one_ocr_fragment(self) -> None:
        deputies = [
            Voter(given_names="Rosalia", surnames="Brown Young", party=PoliticalParty.NUEVA_REPUBLICA),
            Voter(given_names="Kattia", surnames="Cambronero Aguiluz", party=PoliticalParty.PLP),
            Voter(given_names="Gilberto", surnames="Campos Cruz", party=PoliticalParty.PLP),
        ]
        session = VotingSession(name="mocion123", png_path="file.png", deputies=deputies)
        extractor = _FakeExtractor(
            {
                "a_favor": ["Brown Young, Rosalia Cambronero Aguiluz, Campos Cruz, Gilberto"],
                "en_contra": [],
                "no_votacion": [],
            }
        )

        unmatched = session.process_results(extractor=extractor)

        self.assertEqual([], unmatched["a_favor"])
        self.assertEqual(VoteChoice.IN_FAVOR, session.get_vote(deputies[0]))
        self.assertEqual(VoteChoice.IN_FAVOR, session.get_vote(deputies[1]))
        self.assertEqual(VoteChoice.IN_FAVOR, session.get_vote(deputies[2]))

class VotingSessionToDictGroupingTests(unittest.TestCase):
    def test_to_dict_groups_votes_by_party(self) -> None:
        deputies = [
            Voter(name="Ana Perez", party=PoliticalParty.PLN),
            Voter(name="Luis Mora", party=PoliticalParty.PLN),
            Voter(name="Sam Vega", party=PoliticalParty.PUSC),
        ]
        session = VotingSession(name="mocion123", png_path="file.png", deputies=deputies)
        session.register_vote(deputies[0], VoteChoice.IN_FAVOR)
        session.register_vote(deputies[1], VoteChoice.AGAINST)
        session.register_vote(deputies[2], VoteChoice.ABSTENTION)

        data = session.to_dict(group_by_parties=True)

        self.assertIn("votes_by_party", data)
        self.assertEqual(2, len(data["votes_by_party"][PoliticalParty.PLN.value]))
        self.assertEqual(1, len(data["votes_by_party"][PoliticalParty.PUSC.value]))

    def test_to_dict_groups_votes_by_choice(self) -> None:
        deputies = [
            Voter(name="Ana Perez", party=PoliticalParty.PLN),
            Voter(name="Luis Mora", party=PoliticalParty.PUSC),
        ]
        session = VotingSession(name="mocion123", png_path="file.png", deputies=deputies)
        session.register_vote(deputies[0], VoteChoice.IN_FAVOR)

        data = session.to_dict(group_by_vote=True)

        self.assertIn("votes_by_choice", data)
        self.assertEqual(1, len(data["votes_by_choice"]["in_favor"]))
        self.assertEqual(0, len(data["votes_by_choice"]["against"]))
        self.assertEqual(0, len(data["votes_by_choice"]["abstention"]))
        self.assertEqual(1, len(data["votes_by_choice"]["absent"]))

    def test_get_votes_by_seat_returns_vote_choices(self) -> None:
        deputies = [
            Voter(name="Ana Perez", party=PoliticalParty.PLN, seat_number=1),
            Voter(name="Luis Mora", party=PoliticalParty.PUSC, seat_number=2),
        ]
        session = VotingSession(name="mocion123", png_path="file.png", deputies=deputies)
        session.register_vote(deputies[0], VoteChoice.IN_FAVOR)
        session.register_vote(deputies[1], VoteChoice.AGAINST)

        votes_by_seat = session.get_votes_by_seat()

        self.assertEqual(VoteChoice.IN_FAVOR, votes_by_seat[1])
        self.assertEqual(VoteChoice.AGAINST, votes_by_seat[2])
