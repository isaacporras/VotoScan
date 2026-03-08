from pathlib import Path
import json

from text_extractor import TextExtractor


def main() -> None:
    extractor = TextExtractor()

    image_path = Path("votacion_1_example.PNG")

    extracted_text = extractor.extract_text(image_path)
    output_path = Path("resultado_ocr.txt")
    output_path.write_text(extracted_text, encoding="utf-8")

    results = extractor.extract_results(image_path)
    results_path = Path("results.json")
    results_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Text saved to: {output_path.resolve()}")
    print(f"Structured results saved to: {results_path.resolve()}")


if __name__ == "__main__":
    main()
