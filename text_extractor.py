from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

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
        """Extract and return text from the provided image file.

        Args:
            image_path: Path to the image file to process.

        Returns:
            Reconstructed text in approximate reading order
            (top-to-bottom, left-to-right).

        Raises:
            FileNotFoundError: If the image file does not exist.
        """
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
        return cleaned.strip()
