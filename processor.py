from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

from PIL import Image

from models import Assembly, VotingSession
from paths import ASSEMBLY_TEMPLATE, DEBUG_DIR, DEPUTIES_JSON
from seat_renderer import AssemblySeatRenderer


@dataclass(frozen=True)
class ProcessArtifacts:
    json_path: Path
    excel_path: Path
    pdf_path: Path
    preview_image_path: Path
    ocr_debug_path: Path
    ocr_text_debug_path: Path | None
    unmatched_names: dict[str, list[str]]


def process_voting_screenshot(
    screenshot_path: str | Path,
    output_dir: str | Path,
    session_name: str = "voting_session",
    extractor: Any | None = None,
) -> ProcessArtifacts:
    screenshot = Path(screenshot_path)
    if not screenshot.exists():
        raise FileNotFoundError(f"Screenshot file not found: {screenshot}")

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    assembly = Assembly()
    assembly.load_roster_from_json(DEPUTIES_JSON)

    extractor_instance = extractor
    if extractor_instance is None:
        from text_extractor import TextExtractor

        extractor_instance = TextExtractor()

    raw_ocr_results = extractor_instance.extract_results(screenshot)
    if not isinstance(raw_ocr_results, dict):
        raise ValueError("extractor must return a dictionary")

    raw_ocr_text = _extract_raw_ocr_text(extractor_instance, screenshot)
    ocr_debug_path = _write_ocr_debug_output(
        screenshot_path=screenshot,
        session_name=session_name,
        raw_ocr_results=raw_ocr_results,
        raw_ocr_text=raw_ocr_text,
    )
    ocr_text_debug_path = _write_ocr_text_debug_output(
        screenshot_path=screenshot,
        session_name=session_name,
        raw_ocr_text=raw_ocr_text,
    )

    voting_session = VotingSession(
        name=session_name,
        png_path=screenshot,
        deputies=assembly.deputies,
    )
    unmatched = voting_session.process_results(
        extractor=_StaticExtractor(raw_ocr_results)
    )

    results = {
        "voting_session": voting_session.to_dict(group_by_parties=True, group_by_vote=True),
        "unmatched_ocr_names": unmatched,
    }

    json_path = target_dir / "results.json"
    json_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    excel_path = voting_session.to_excel(
        target_dir / "results.xlsx",
        group_by_parties=True,
        group_by_vote=True,
    )

    preview_image_path = screenshot
    if ASSEMBLY_TEMPLATE.exists():
        preview_image_path = AssemblySeatRenderer().render(
            assembly=assembly,
            template_path=ASSEMBLY_TEMPLATE,
            output_path=target_dir / "asamblea_seats_labeled.png",
            vote_choices_by_seat=voting_session.get_votes_by_seat(),
        )

    pdf_path = _build_pdf_report(preview_image_path, target_dir / "voting_report.pdf")
    return ProcessArtifacts(
        json_path=json_path,
        excel_path=excel_path,
        pdf_path=pdf_path,
        preview_image_path=preview_image_path,
        ocr_debug_path=ocr_debug_path,
        ocr_text_debug_path=ocr_text_debug_path,
        unmatched_names=unmatched,
    )


def _build_pdf_report(image_path: str | Path, pdf_path: str | Path) -> Path:
    source = Path(image_path)
    target = Path(pdf_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as image:
        rgb_image = image.convert("RGB")
        rgb_image.save(target, "PDF", resolution=100.0)

    return target


def _write_ocr_debug_output(
    screenshot_path: Path,
    session_name: str,
    raw_ocr_results: dict[str, Any],
    raw_ocr_text: str | None,
) -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    safe_session_name = _safe_slug(session_name or screenshot_path.stem)
    debug_path = DEBUG_DIR / f"{safe_session_name}_ocr_output.json"
    payload = {
        "session_name": session_name,
        "screenshot_path": str(screenshot_path),
        "raw_ocr_results": raw_ocr_results,
        "raw_ocr_text_path": str(DEBUG_DIR / f"{safe_session_name}_ocr_output.txt") if raw_ocr_text is not None else None,
    }
    debug_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return debug_path


def _write_ocr_text_debug_output(
    screenshot_path: Path,
    session_name: str,
    raw_ocr_text: str | None,
) -> Path | None:
    if raw_ocr_text is None:
        return None

    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    safe_session_name = _safe_slug(session_name or screenshot_path.stem)
    debug_path = DEBUG_DIR / f"{safe_session_name}_ocr_output.txt"
    debug_path.write_text(raw_ocr_text, encoding="utf-8")
    return debug_path


def _extract_raw_ocr_text(extractor: Any, screenshot_path: Path) -> str | None:
    extract_text = getattr(extractor, "extract_text", None)
    if not callable(extract_text):
        return None

    raw_text = extract_text(screenshot_path)
    if raw_text is None:
        return None
    return str(raw_text)


def _safe_slug(value: str) -> str:
    sanitized = "".join(ch if ch.isalnum() else "_" for ch in value.strip().lower())
    return sanitized.strip("_") or "voting_session"


class _StaticExtractor:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def extract_results(self, _path: str | Path) -> dict[str, Any]:
        return self.payload
