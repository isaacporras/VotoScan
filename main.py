from pathlib import Path
import json

from models import Assembly, VotingSession


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

    print(f"Voting session processed. Results saved to: {results_path.resolve()}")


if __name__ == "__main__":
    main()
