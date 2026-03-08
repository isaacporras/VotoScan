from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

from PIL import Image
import pytesseract
from pytesseract import Output

PathLike = str | Path


@dataclass
class OCRToken:
    """Represents a single OCR-detected token and its image coordinates."""

    text: str
    left: int
    top: int
    height: int


class TextExtractor:
    """Extracts text from an image using Tesseract OCR."""

    def __init__(self) -> None:
        """Create a text extractor instance.

        Assumes `tesseract` is available in the system PATH.
        """
        pass

    def extract_text(self, image_path: PathLike) -> str:
        """Extract and return text from the provided image file."""
        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_file}")

        with Image.open(image_file) as image:
            data = pytesseract.image_to_data(
                image,
                output_type=Output.DICT,
                config="--oem 3 --psm 6",
            )

        tokens = self._tokens_from_data(data)
        if not tokens:
            return ""

        return self._build_text(tokens)

    def extract_results(self, image_path: PathLike) -> dict[str, object]:
        """Extract voting sections and names into a structured dictionary."""
        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_file}")

        with Image.open(image_file) as image:
            data = pytesseract.image_to_data(
                image,
                output_type=Output.DICT,
                config="--oem 3 --psm 6",
            )

            sections = self._detect_sections(data, image.height)
            column_bounds = self._column_bounds(image.width)

            results: dict[str, object] = {
                "votos_a_favor": 0,
                "votos_en_contra": 0,
                "votos_no_votacion": 0,
                "total": 0,
                "a_favor": [],
                "en_contra": [],
                "no_votacion": [],
            }

            key_map = {
                "a_favor": "votos_a_favor",
                "en_contra": "votos_en_contra",
                "no_votacion": "votos_no_votacion",
            }

            for section_key in ("a_favor", "en_contra", "no_votacion"):
                section_info = sections[section_key]
                y0, y1 = section_info["range"]
                expected_count = int(section_info["count"])

                names: list[str] = []
                for x0, x1 in column_bounds:
                    crop = image.crop((x0, y0, x1, y1))
                    block_text = pytesseract.image_to_string(
                        crop,
                        config="--oem 3 --psm 6",
                    )
                    names.extend(self._names_from_block(block_text))

                names = self._dedupe_preserving_order(names)
                if expected_count > 0 and len(names) > expected_count:
                    names = names[:expected_count]

                results[key_map[section_key]] = expected_count if expected_count > 0 else len(names)
                results[section_key] = names

            results["total"] = (
                int(results["votos_a_favor"])
                + int(results["votos_en_contra"])
                + int(results["votos_no_votacion"])
            )

            return results

    def _tokens_from_data(self, data: dict[str, list[str] | list[int]]) -> list[OCRToken]:
        """Convert raw Tesseract output into typed OCR tokens."""
        tokens: list[OCRToken] = []
        texts = data["text"]
        confidences = data["conf"]
        left_positions = data["left"]
        top_positions = data["top"]
        heights = data["height"]

        for i, raw_text in enumerate(texts):
            text = str(raw_text).strip()
            if not text:
                continue

            raw_confidence = str(confidences[i])
            confidence = int(raw_confidence) if raw_confidence != "-1" else -1
            if confidence < 0:
                continue

            tokens.append(
                OCRToken(
                    text=text,
                    left=int(left_positions[i]),
                    top=int(top_positions[i]),
                    height=int(heights[i]),
                )
            )

        return tokens

    def _build_text(self, tokens: list[OCRToken]) -> str:
        """Rebuild multiline text by sorting tokens by screen coordinates."""
        tokens.sort(key=lambda token: (token.top, token.left))
        average_height = sum(token.height for token in tokens) / len(tokens)
        line_tolerance = max(12, int(average_height * 0.6))

        lines: list[dict[str, int | list[OCRToken]]] = []

        for token in tokens:
            if not lines:
                lines.append({"y": token.top, "tokens": [token]})
                continue

            last_y = int(lines[-1]["y"])
            if abs(token.top - last_y) <= line_tolerance:
                line_tokens = lines[-1]["tokens"]
                assert isinstance(line_tokens, list)
                line_tokens.append(token)
                lines[-1]["y"] = int((last_y + token.top) / 2)
            else:
                lines.append({"y": token.top, "tokens": [token]})

        rows: list[str] = []
        for line in lines:
            line_tokens = line["tokens"]
            assert isinstance(line_tokens, list)
            ordered_tokens = sorted(line_tokens, key=lambda token: token.left)
            raw_line = " ".join(token.text for token in ordered_tokens)
            cleaned_line = self._clean_line(raw_line)
            if cleaned_line:
                rows.append(cleaned_line)

        return "\n".join(rows)

    def _detect_sections(
        self, data: dict[str, list[str] | list[int]], image_height: int
    ) -> dict[str, dict[str, object]]:
        """Find y-ranges for each voting section and their reported counts."""
        text_values = data["text"]
        top_values = data["top"]

        favor_y: int | None = None
        contra_y: int | None = None
        no_vot_y: int | None = None

        for i, raw_text in enumerate(text_values):
            text = str(raw_text).strip()
            if not text:
                continue

            normalized = self._normalize_text(text)
            top = int(top_values[i])

            if normalized == "favor":
                favor_y = top if favor_y is None else min(favor_y, top)
            elif "contra" in normalized:
                contra_y = top if contra_y is None else min(contra_y, top)
            elif normalized.startswith("novot"):
                no_vot_y = top if no_vot_y is None else min(no_vot_y, top)

        # Fallbacks for template-like images if OCR misses section headers.
        if favor_y is None:
            favor_y = int(image_height * 0.07)
        if contra_y is None:
            contra_y = int(image_height * 0.24)
        if no_vot_y is None:
            no_vot_y = int(image_height * 0.46)

        headers = [
            ("a_favor", favor_y),
            ("en_contra", contra_y),
            ("no_votacion", no_vot_y),
        ]
        headers.sort(key=lambda item: item[1])

        result: dict[str, dict[str, object]] = {}
        for idx, (key, header_y) in enumerate(headers):
            next_header_y = headers[idx + 1][1] if idx + 1 < len(headers) else image_height
            y0 = max(0, header_y + 26)
            y1 = max(y0 + 1, next_header_y - 6)
            count = self._extract_count_for_header(data, header_y)
            result[key] = {"range": (y0, y1), "count": count}

        return result

    def _extract_count_for_header(self, data: dict[str, list[str] | list[int]], header_y: int) -> int:
        """Extract numeric count shown in section header line (e.g. Voto: 9)."""
        text_values = data["text"]
        top_values = data["top"]

        candidates: list[tuple[int, int]] = []
        for i, raw_text in enumerate(text_values):
            text = str(raw_text).strip()
            if not text:
                continue

            top = int(top_values[i])
            if top < header_y - 4 or top > header_y + 26:
                continue

            match = re.search(r"\d+", text)
            if match:
                candidates.append((top, int(match.group())))

        if not candidates:
            return 0

        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _column_bounds(self, image_width: int) -> list[tuple[int, int]]:
        """Return 4 table-column crop bounds based on image width."""
        bounds: list[tuple[int, int]] = []
        step = image_width / 4.0
        for idx in range(4):
            x0 = int(idx * step) + 8
            x1 = int((idx + 1) * step) - 8
            bounds.append((x0, x1))
        return bounds

    def _names_from_block(self, block_text: str) -> list[str]:
        """Parse probable names from an OCR text block."""
        names: list[str] = []
        for raw_line in block_text.splitlines():
            line = self._clean_line(raw_line)
            if not line or "," not in line:
                continue

            pieces = re.split(r"[|\\]+", line)
            for piece in pieces:
                candidate = self._clean_line(piece)
                if not candidate or "," not in candidate:
                    continue
                names.append(candidate)

        return names

    def _dedupe_preserving_order(self, values: list[str]) -> list[str]:
        """Deduplicate string list while preserving first-seen order."""
        seen: set[str] = set()
        ordered: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            ordered.append(value)
        return ordered

    def _normalize_text(self, value: str) -> str:
        """Normalize OCR token for robust matching (headers/keywords)."""
        base = unicodedata.normalize("NFKD", value)
        ascii_only = "".join(ch for ch in base if not unicodedata.combining(ch))
        return re.sub(r"[^a-z0-9]", "", ascii_only.lower())

    def _clean_line(self, line: str) -> str:
        """Remove common OCR noise characters and normalize spacing."""
        noise_map = str.maketrans(
            {
                "(": " ",
                ")": " ",
                "[": " ",
                "]": " ",
                "{": " ",
                "}": " ",
                "|": " ",
            }
        )
        cleaned = line.translate(noise_map)
        cleaned = re.sub(r"\.{2,}", "", cleaned)
        cleaned = re.sub(r"\s+,", ",", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned.strip(" -,_")
