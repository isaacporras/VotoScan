from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFont

from models import Assembly, VoteChoice


@dataclass(frozen=True)
class SeatCircle:
    x: int
    y: int
    radius: int


# Fixed layout extracted once from assets/templates/asamblea_seats_template.png
# Ordered left-to-right, top-to-bottom, matching seat_number.
DEFAULT_SEAT_LAYOUT: tuple[SeatCircle, ...] = (
    SeatCircle(245, 170, 38),
    SeatCircle(336, 170, 38),
    SeatCircle(425, 170, 38),
    SeatCircle(518, 170, 38),
    SeatCircle(613, 170, 38),
    SeatCircle(711, 170, 38),
    SeatCircle(810, 170, 38),
    SeatCircle(909, 170, 38),
    SeatCircle(1007, 170, 38),
    SeatCircle(1106, 170, 38),
    SeatCircle(1205, 170, 38),
    SeatCircle(1303, 170, 38),
    SeatCircle(1394, 170, 38),
    SeatCircle(1484, 172, 38),
    SeatCircle(245, 297, 38),
    SeatCircle(335, 297, 38),
    SeatCircle(425, 297, 38),
    SeatCircle(518, 297, 38),
    SeatCircle(614, 297, 38),
    SeatCircle(712, 297, 38),
    SeatCircle(810, 297, 38),
    SeatCircle(909, 297, 38),
    SeatCircle(1007, 297, 38),
    SeatCircle(1106, 297, 38),
    SeatCircle(1205, 297, 38),
    SeatCircle(1303, 297, 38),
    SeatCircle(1394, 297, 38),
    SeatCircle(115, 386, 38),
    SeatCircle(115, 495, 38),
    SeatCircle(115, 612, 38),
    SeatCircle(246, 692, 37),
    SeatCircle(336, 692, 37),
    SeatCircle(425, 692, 37),
    SeatCircle(519, 692, 37),
    SeatCircle(614, 692, 37),
    SeatCircle(712, 692, 37),
    SeatCircle(810, 692, 37),
    SeatCircle(909, 692, 37),
    SeatCircle(1008, 692, 37),
    SeatCircle(1106, 692, 37),
    SeatCircle(1205, 692, 37),
    SeatCircle(1303, 692, 37),
    SeatCircle(1394, 692, 37),
    SeatCircle(245, 807, 37),
    SeatCircle(336, 807, 37),
    SeatCircle(425, 807, 37),
    SeatCircle(519, 807, 37),
    SeatCircle(614, 807, 37),
    SeatCircle(712, 807, 37),
    SeatCircle(810, 807, 37),
    SeatCircle(910, 807, 37),
    SeatCircle(1008, 807, 37),
    SeatCircle(1107, 807, 37),
    SeatCircle(1205, 807, 37),
    SeatCircle(1304, 807, 37),
    SeatCircle(1394, 807, 37),
    SeatCircle(1484, 804, 38),
)


class AssemblySeatRenderer:
    """Draw deputy names below each seat circle in a seating template image."""

    def __init__(
        self,
        threshold: int = 130,
        row_tolerance: int = 36,
        use_fixed_layout: bool = True,
    ) -> None:
        self.threshold = threshold
        self.row_tolerance = row_tolerance
        self.use_fixed_layout = use_fixed_layout

    def render(
        self,
        assembly: Assembly,
        template_path: str | Path,
        output_path: str | Path,
        vote_choices_by_seat: dict[int, VoteChoice | str] | None = None,
    ) -> Path:
        assignments = assembly.get_seat_assignments()
        if not assignments:
            raise ValueError("assembly has no deputies to render")

        image_path = Path(template_path)
        if not image_path.exists():
            raise FileNotFoundError(f"template image not found: {image_path}")

        with Image.open(image_path) as base_image:
            image = base_image.convert("RGBA")

        circles = list(DEFAULT_SEAT_LAYOUT) if self.use_fixed_layout else self._detect_seat_circles(image)
        if len(circles) < len(assignments):
            raise ValueError(
                f"detected {len(circles)} seat circles but assembly has {len(assignments)} deputies"
            )

        draw = ImageDraw.Draw(image)
        if vote_choices_by_seat:
            self._paint_vote_results(draw=draw, circles=circles, vote_choices_by_seat=vote_choices_by_seat)
        font = self._load_font()

        for assignment in assignments:
            seat_number = assignment["seat_number"]
            if not isinstance(seat_number, int) or seat_number < 1:
                continue
            if seat_number > len(circles):
                continue

            circle = circles[seat_number - 1]
            label = self._short_name(str(assignment["name"]))
            self._draw_centered_label(
                draw=draw,
                font=font,
                text=label,
                center_x=circle.x,
                top_y=circle.y + circle.radius + 8,
            )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output)
        return output

    def _paint_vote_results(
        self,
        draw: ImageDraw.ImageDraw,
        circles: list[SeatCircle],
        vote_choices_by_seat: dict[int, VoteChoice | str],
    ) -> None:
        color_by_choice = {
            VoteChoice.IN_FAVOR.value: (35, 170, 85, 170),
            VoteChoice.AGAINST.value: (210, 55, 55, 170),
            VoteChoice.ABSTENTION.value: (125, 125, 125, 170),
            VoteChoice.ABSENT.value: (125, 125, 125, 170),
        }
        for seat_number, choice in vote_choices_by_seat.items():
            if seat_number < 1 or seat_number > len(circles):
                continue
            normalized_choice = choice.value if isinstance(choice, VoteChoice) else str(choice).strip().lower()
            fill_color = color_by_choice.get(normalized_choice)
            if fill_color is None:
                continue

            circle = circles[seat_number - 1]
            inset = 5
            left = circle.x - circle.radius + inset
            top = circle.y - circle.radius + inset
            right = circle.x + circle.radius - inset
            bottom = circle.y + circle.radius - inset
            draw.ellipse((left, top, right, bottom), fill=fill_color)

    def discover_seat_map(
        self,
        template_path: str | Path,
        out_json_path: str | Path | None = None,
        out_debug_path: str | Path | None = None,
    ) -> dict[str, list[dict[str, int]]]:
        image_path = Path(template_path)
        if not image_path.exists():
            raise FileNotFoundError(f"template image not found: {image_path}")

        with Image.open(image_path) as base_image:
            image = base_image.convert("RGBA")

        circles = self._detect_seat_circles(image)
        payload = {
            "seats": [
                {"seat_number": idx + 1, "x": c.x, "y": c.y, "radius": c.radius}
                for idx, c in enumerate(circles)
            ]
        }

        if out_json_path is not None:
            target = Path(out_json_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        if out_debug_path is not None:
            debug_image = image.copy()
            draw = ImageDraw.Draw(debug_image)
            font = self._load_font()
            for idx, circle in enumerate(circles, start=1):
                draw.text((circle.x - 10, circle.y - 8), str(idx), fill=(255, 80, 80, 255), font=font)
            target_img = Path(out_debug_path)
            target_img.parent.mkdir(parents=True, exist_ok=True)
            debug_image.save(target_img)

        return payload

    def _detect_seat_circles(self, image: Image.Image) -> list[SeatCircle]:
        gray = image.convert("L")
        width, height = gray.size
        pixels = gray.load()

        visited = [[False for _ in range(width)] for _ in range(height)]
        circles: list[SeatCircle] = []

        for y in range(height):
            for x in range(width):
                if visited[y][x]:
                    continue
                visited[y][x] = True

                if pixels[x, y] < self.threshold:
                    continue

                component = self._collect_component(pixels, visited, x, y, width, height)
                if component is None:
                    continue

                circles.append(component)

        circles = self._dedupe_close_circles(circles)
        return self._sort_circles_by_layout(circles)

    def _collect_component(
        self,
        pixels,
        visited: list[list[bool]],
        start_x: int,
        start_y: int,
        width: int,
        height: int,
    ) -> SeatCircle | None:
        queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
        points: list[tuple[int, int]] = []

        min_x = max_x = start_x
        min_y = max_y = start_y

        while queue:
            x, y = queue.popleft()
            points.append((x, y))

            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                if visited[ny][nx]:
                    continue
                visited[ny][nx] = True
                if pixels[nx, ny] >= self.threshold:
                    queue.append((nx, ny))

        area = len(points)
        box_w = (max_x - min_x) + 1
        box_h = (max_y - min_y) + 1
        if area < 160 or area > 2600:
            return None
        if box_w < 26 or box_h < 26 or box_w > 120 or box_h > 120:
            return None

        ratio = box_w / max(1, box_h)
        if ratio < 0.65 or ratio > 1.35:
            return None

        center_x = int((min_x + max_x) / 2)
        center_y = int((min_y + max_y) / 2)
        radius = int(min(box_w, box_h) / 2)
        return SeatCircle(x=center_x, y=center_y, radius=radius)

    def _dedupe_close_circles(self, circles: list[SeatCircle]) -> list[SeatCircle]:
        circles = sorted(circles, key=lambda c: (c.y, c.x))
        deduped: list[SeatCircle] = []

        for circle in circles:
            duplicate = False
            for existing in deduped:
                if abs(existing.x - circle.x) <= 10 and abs(existing.y - circle.y) <= 10:
                    duplicate = True
                    break
            if not duplicate:
                deduped.append(circle)

        return deduped

    def _sort_circles_by_layout(self, circles: list[SeatCircle]) -> list[SeatCircle]:
        if not circles:
            return []

        circles_sorted = sorted(circles, key=lambda c: (c.y, c.x))
        rows: list[list[SeatCircle]] = []

        for circle in circles_sorted:
            if not rows:
                rows.append([circle])
                continue

            row_avg_y = sum(item.y for item in rows[-1]) / len(rows[-1])
            if abs(circle.y - row_avg_y) <= self.row_tolerance:
                rows[-1].append(circle)
            else:
                rows.append([circle])

        ordered: list[SeatCircle] = []
        for row in rows:
            ordered.extend(sorted(row, key=lambda c: c.x))
        return ordered

    def _load_font(self) -> ImageFont.ImageFont:
        for candidate in ("arial.ttf", "segoeui.ttf"):
            try:
                return ImageFont.truetype(candidate, 16)
            except OSError:
                continue
        return ImageFont.load_default()

    def _short_name(self, full_name: str) -> str:
        parts = [part for part in full_name.split() if part]
        if len(parts) >= 2:
            connector_articles = {"la", "las", "los", "el"}
            for idx in range(1, len(parts) - 1):
                if parts[idx].lower() != "de":
                    continue
                next_token = parts[idx + 1]
                if next_token.lower() in connector_articles:
                    continue
                return f"{parts[0]}\nde {next_token}"

            # Fallback: use first surname (not second surname).
            if len(parts) >= 5 and parts[1].lower() == "de" and parts[2].lower() in connector_articles:
                # Example: "Maria de los Angeles Rojas"
                return f"{parts[0]}\n{parts[4]}"
            if len(parts) >= 4:
                # Example: "Jorge Antonio Rojas Lopez" -> "Jorge / Rojas"
                return f"{parts[0]}\n{parts[2]}"
            if len(parts) >= 3:
                # Example: "Ada Acuna Castro" -> "Ada / Acuna"
                return f"{parts[0]}\n{parts[1]}"
            return f"{parts[0]}\n{parts[1]}"
        return full_name

    def _draw_centered_label(
        self,
        draw: ImageDraw.ImageDraw,
        font: ImageFont.ImageFont,
        text: str,
        center_x: int,
        top_y: int,
    ) -> None:
        bbox = draw.textbbox((0, 0), text=text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = int(center_x - (text_w / 2))
        y = int(top_y)

        draw.rectangle((x - 2, y - 1, x + text_w + 2, y + text_h + 1), fill=(0, 0, 0, 180))
        draw.text((x, y), text=text, fill=(235, 235, 235, 255), font=font)
