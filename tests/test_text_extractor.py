import unittest

from text_extractor import TextExtractor


class TextExtractorNameParsingTests(unittest.TestCase):
    def test_names_from_block_keeps_whole_line_when_ocr_groups_multiple_people(self) -> None:
        extractor = TextExtractor()

        names = extractor._names_from_block(
            "Brown Young, Rosalia Cambronero Aguiluz, Campos Cruz, Gilberto"
        )

        self.assertEqual(
            [
                "Brown Young, Rosalia Cambronero Aguiluz, Campos Cruz, Gilberto",
            ],
            names,
        )

    def test_names_from_block_splits_explicit_separators_only(self) -> None:
        extractor = TextExtractor()

        names = extractor._names_from_block(
            "Brown Young, Rosalia Cambronero Aguiluz, Campos Cruz, Gilberto Castro Mora, Vanessa"
            "\\Vargas Quirés, Daniel"
        )

        self.assertEqual(
            [
                "Brown Young, Rosalia Cambronero Aguiluz, Campos Cruz, Gilberto Castro Mora, Vanessa",
                "Vargas Quirés, Daniel",
            ],
            names,
        )

    def test_names_from_block_preserves_simple_name_entries(self) -> None:
        extractor = TextExtractor()

        names = extractor._names_from_block("Rojas Salas, Daniela")

        self.assertEqual(["Rojas Salas, Daniela"], names)


if __name__ == "__main__":
    unittest.main()
