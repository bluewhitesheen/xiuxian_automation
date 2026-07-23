import argparse
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


TOP_COLORS = 7
DEFAULT_FILTER_HEX = ["efe7de", "ffffff", "429e52", "4a9e5a", "efe3d6", "4aa25a", "4a9e52"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate color distribution bars from a result directory."
    )
    parser.add_argument(
        "result_dir",
        nargs="?",
        default="result",
        help="Path to folder containing images.",
    )
    return parser.parse_args()


def hex_to_rgb(hex_color):
    hex_color = hex_color.strip().lower().lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(color):
    return "{0:02x}{1:02x}{2:02x}".format(color[0], color[1], color[2])


def get_filter_set(filter_hex):
    return {hex_to_rgb(hex_color) for hex_color in filter_hex}


def _iter_rgb_pixels(image):
    try:
        data = image.tobytes()
        if len(data) % 3 != 0:
            raise ValueError("unexpected byte length")
        return [(data[i], data[i + 1], data[i + 2]) for i in range(0, len(data), 3)]
    except Exception:
        # fallback for environments with unusual formats
        return [tuple(pixel) for pixel in image.getdata()]


def _top_colors_for_image(image_path, filter_colors, top_colors):
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        pixels = _iter_rgb_pixels(rgb)

    total_pixels = len(pixels)
    if total_pixels == 0:
        return []

    counts = Counter(pixels)
    visible_colors = [(color, cnt) for color, cnt in counts.items() if color not in filter_colors]
    if not visible_colors:
        return []

    visible_colors = sorted(visible_colors, key=lambda kv: kv[1], reverse=True)
    visible_colors = visible_colors[:top_colors]
    return [
        (rgb_to_hex(color), (cnt * 100.0) / total_pixels, color)
        for color, cnt in visible_colors
    ]


def _build_no_data_image(message):
    canvas = Image.new("RGB", (520, 120), color=(250, 250, 250))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 46), message, fill=(60, 60, 60), font=ImageFont.load_default())
    return canvas


def _build_color_bar_image(entries):
    row_height = 40
    label_width = 140
    bar_width = 640
    bar_height = 20
    left_padding = 10
    top_padding = 10

    rows = list(entries)
    font = ImageFont.load_default()
    canvas_w = left_padding * 2 + label_width + bar_width
    canvas_h = top_padding * 2 + len(rows) * row_height
    canvas = Image.new("RGB", (canvas_w, canvas_h), color=(245, 245, 245))
    draw = ImageDraw.Draw(canvas)

    for idx, (filename, colors) in enumerate(rows):
        y = top_padding + idx * row_height
        draw.text((left_padding, y + 2), filename, fill=(20, 20, 20), font=font)

        bar_x0 = left_padding + label_width
        bar_y0 = y + (row_height - bar_height) // 2
        bar_x1 = bar_x0 + bar_width
        bar_y1 = bar_y0 + bar_height

        draw.rectangle((bar_x0, bar_y0, bar_x1, bar_y1), outline=(30, 30, 30), fill=(220, 220, 220))

        color_count = len(colors)
        if color_count == 0:
            continue

        segment_width = bar_width / float(color_count)
        x = bar_x0
        for idx_color, (_, _, rgb) in enumerate(colors):
            if idx_color == color_count - 1:
                current_width = bar_x1 - x
            else:
                current_width = int(round(segment_width))
            if current_width <= 0:
                continue
            draw.rectangle((x, bar_y0, x + current_width, bar_y1), fill=rgb)
            x += current_width
            if x >= bar_x1:
                break

        if x < bar_x1:
            draw.rectangle((x, bar_y0, bar_x1, bar_y1), fill=(220, 220, 220))

    return canvas


def _format_line(filename, colors):
    parts = ["{}: {:.1f}%".format(color_hex, percent) for color_hex, percent, _ in colors]
    return "{}: {}".format(filename, " ".join(parts))


def analyze_result_dir(
    result_dir="result",
    top_colors=TOP_COLORS,
    filter_hex=None,
    show_popup=True,
    print_console=False,
):
    """
    Build color distribution bars for a result directory and return PIL image.
    Optionally print color percentages to console.
    """
    if filter_hex is None:
        filter_hex = DEFAULT_FILTER_HEX

    result_dir_path = Path(result_dir)
    if not result_dir_path.exists() or not result_dir_path.is_dir():
        raise FileNotFoundError("folder not found: {}".format(result_dir_path))

    exts = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}
    image_files = sorted(
        p for p in result_dir_path.iterdir() if p.is_file() and p.suffix.lower() in exts
    )

    filter_colors = get_filter_set(filter_hex)
    rows = []

    for img_path in image_files:
        colors = _top_colors_for_image(img_path, filter_colors, top_colors)
        if colors:
            rows.append((img_path.name, colors))

    if rows:
        bar_image = _build_color_bar_image(rows)
    else:
        bar_image = _build_no_data_image("No visible color bars to show (all pixels are filtered).")

    if print_console:
        if rows:
            for filename, colors in rows:
                print(_format_line(filename, colors))

    if show_popup:
        bar_image.show()
    return bar_image


def main():
    args = parse_args()
    analyze_result_dir(args.result_dir, show_popup=True, print_console=True)


if __name__ == "__main__":
    main()
