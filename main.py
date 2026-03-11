import json

from models import Assembly, VotingSession
from paths import (
    ASSEMBLY_LABELED,
    ASSEMBLY_TEMPLATE,
    DEPUTIES_JSON,
    RESULTS_JSON,
    RESULTS_XLSX,
    VOTING_SCREENSHOT,
)
from seat_renderer import AssemblySeatRenderer


def main() -> None:
    assembly = Assembly()
    assembly.load_roster_from_json(DEPUTIES_JSON)

    voting_session = VotingSession(
        name="mocion123",
        png_path=VOTING_SCREENSHOT,
        deputies=assembly.deputies,
    )
    unmatched = voting_session.process_results()

    results = {
        "voting_session": voting_session.to_dict(group_by_parties=True),
        "unmatched_ocr_names": unmatched,
    }

    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    excel_path = voting_session.to_excel(
        RESULTS_XLSX,
        group_by_parties=True,
        group_by_vote=True,
    )

    if ASSEMBLY_TEMPLATE.exists():
        seat_image_path = AssemblySeatRenderer().render(
            assembly=assembly,
            template_path=ASSEMBLY_TEMPLATE,
            output_path=ASSEMBLY_LABELED,
            vote_choices_by_seat=voting_session.get_votes_by_seat(),
        )
        print(f"Assembly seats image saved to: {seat_image_path.resolve()}")
    else:
        print(
            "Assembly seats template not found. "
            f"Expected file: {ASSEMBLY_TEMPLATE}"
        )

    print(f"Voting session processed. JSON saved to: {RESULTS_JSON.resolve()}")
    print(f"Voting session processed. Excel saved to: {excel_path.resolve()}")


if __name__ == "__main__":
    main()
