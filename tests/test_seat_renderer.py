import unittest
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw

from models import Assembly, PoliticalParty, VoteChoice, Voter
from seat_renderer import AssemblySeatRenderer


class AssemblySeatRendererTests(unittest.TestCase):
    def test_short_name_supports_de_connector(self) -> None:
        renderer = AssemblySeatRenderer()
        self.assertEqual("Vanessa\nde Paul", renderer._short_name("Vanessa de Paul Castro Mora"))
        self.assertEqual("María\nRojas", renderer._short_name("María de los Ángeles Rojas"))
        self.assertEqual("Jorge\nRojas", renderer._short_name("Jorge Antonio Rojas López"))
        self.assertEqual("Ada\nAcuña", renderer._short_name("Ada Acuña Castro"))

    def test_render_draws_labels_on_detected_seats(self) -> None:
        temp_dir = Path("tests/.tmp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        template_path = temp_dir / f"seats_template_{uuid4().hex}.png"
        output_path = temp_dir / f"seats_output_{uuid4().hex}.png"

        image = Image.new("RGB", (420, 220), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)
        for center_x, center_y in ((80, 70), (210, 70), (340, 70)):
            draw.ellipse(
                (center_x - 26, center_y - 26, center_x + 26, center_y + 26),
                outline=(220, 220, 220),
                width=4,
            )
        image.save(template_path)

        assembly = Assembly()
        assembly.add_deputy(Voter(name="Ana Perez", party=PoliticalParty.PLN, seat_number=1))
        assembly.add_deputy(Voter(name="Luis Mora", party=PoliticalParty.PUSC, seat_number=2))
        assembly.add_deputy(Voter(name="Sam Vega", party=PoliticalParty.PLP, seat_number=3))

        renderer = AssemblySeatRenderer()
        generated = renderer.render(assembly, template_path, output_path)

        self.assertTrue(generated.exists())
        self.assertGreater(generated.stat().st_size, 0)

    def test_render_applies_vote_colors(self) -> None:
        temp_dir = Path("tests/.tmp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        template_path = temp_dir / f"seats_template_{uuid4().hex}.png"
        output_path = temp_dir / f"seats_output_{uuid4().hex}.png"

        image = Image.new("RGBA", (1600, 1024), color=(0, 0, 0, 255))
        draw = ImageDraw.Draw(image)
        for center_x, center_y in ((245, 170), (336, 170), (425, 170)):
            draw.ellipse(
                (center_x - 38, center_y - 38, center_x + 38, center_y + 38),
                outline=(220, 220, 220, 255),
                width=4,
            )
        image.save(template_path)

        assembly = Assembly()
        assembly.add_deputy(Voter(name="Ana Perez", party=PoliticalParty.PLN, seat_number=1))
        assembly.add_deputy(Voter(name="Luis Mora", party=PoliticalParty.PUSC, seat_number=2))
        assembly.add_deputy(Voter(name="Sam Vega", party=PoliticalParty.PLP, seat_number=3))

        renderer = AssemblySeatRenderer()
        renderer.render(
            assembly=assembly,
            template_path=template_path,
            output_path=output_path,
            vote_choices_by_seat={
                1: VoteChoice.IN_FAVOR,
                2: VoteChoice.AGAINST,
                3: VoteChoice.ABSTENTION,
            },
        )

        out = Image.open(output_path).convert("RGBA")
        c1 = out.getpixel((245, 170))
        c2 = out.getpixel((336, 170))
        c3 = out.getpixel((425, 170))

        self.assertGreater(c1[1], c1[0])  # green dominant
        self.assertGreater(c2[0], c2[1])  # red dominant
        self.assertTrue(abs(c3[0] - c3[1]) < 20 and abs(c3[1] - c3[2]) < 20)  # gray-ish


if __name__ == "__main__":
    unittest.main()
