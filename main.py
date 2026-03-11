from pathlib import Path
import json

from models import Assembly, VotingSession
from seat_renderer import AssemblySeatRenderer


def main() -> None:
    assembly = Assembly()
    assembly.load_roster_from_json("deputies.json")

    voting_session = VotingSession(
        name="mocion123",
        png_path="votacion_1_example.PNG",
        deputies=assembly.deputies,
    )
    unmatched = voting_session.process_results()

    results = {
        "voting_session": voting_session.to_dict(group_by_parties=True),
        "unmatched_ocr_names": unmatched,
    }

    results_path = Path("results.json")
    results_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    excel_path = voting_session.to_excel(
        "results.xlsx",
        group_by_parties=True,
        group_by_vote=True,
    )

    seats_template = Path("asamblea_seats_template.png")
    if seats_template.exists():
        seat_image_path = AssemblySeatRenderer().render(
            assembly=assembly,
            template_path=seats_template,
            output_path="asamblea_seats_labeled.png",
            vote_choices_by_seat=voting_session.get_votes_by_seat(),
        )
        print(f"Assembly seats image saved to: {seat_image_path.resolve()}")
    else:
        print(
            "Assembly seats template not found. "
            "Expected file: asamblea_seats_template.png"
        )

    print(f"Voting session processed. JSON saved to: {results_path.resolve()}")
    print(f"Voting session processed. Excel saved to: {excel_path.resolve()}")


if __name__ == "__main__":
    main()
