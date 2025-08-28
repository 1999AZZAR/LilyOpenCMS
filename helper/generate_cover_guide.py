#!/usr/bin/env python3
"""
Generate visual crop/placement guides on top of an image to help design covers.

Features:
- Draw centered crop boxes for common aspect ratios: 4:3, 16:9, 1:1, 3:4
- Draw rule-of-thirds grid
- Draw text-safe areas and baseline guides (for title/subtitle placement)
- Output a PNG with translucent overlays

Usage:
  python helper/generate_cover_guide.py --input /path/to/image.jpg --output /path/to/output.png
  # Optional: choose ratios
  python helper/generate_cover_guide.py --input in.jpg --output out.png --ratios 4:3 16:9 1:1 3:4
"""

import argparse
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont


def parse_ratio(ratio_str: str) -> Tuple[int, int]:
    a, b = ratio_str.split(":")
    return int(a), int(b)


def centered_box_for_ratio(w: int, h: int, target_w: int, target_h: int) -> Tuple[int, int, int, int]:
    # Fit a target aspect box inside (w,h), centered
    image_ratio = w / h
    target_ratio = target_w / target_h
    if image_ratio > target_ratio:
        # Limit by height
        box_h = h
        box_w = int(round(box_h * target_ratio))
    else:
        # Limit by width
        box_w = w
        box_h = int(round(box_w / target_ratio))
    x0 = (w - box_w) // 2
    y0 = (h - box_h) // 2
    x1 = x0 + box_w
    y1 = y0 + box_h
    return x0, y0, x1, y1


def draw_label(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, fill=(255, 255, 255), stroke=(0, 0, 0)):
    x, y = xy
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    # simple stroke
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        draw.text((x+dx, y+dy), text, fill=stroke, font=font)
    draw.text((x, y), text, fill=fill, font=font)


def draw_rule_of_thirds(draw: ImageDraw.ImageDraw, w: int, h: int, color=(255,255,0,120)):
    # Two vertical, two horizontal
    v1 = w // 3
    v2 = 2 * w // 3
    h1 = h // 3
    h2 = 2 * h // 3
    draw.line([(v1, 0), (v1, h)], fill=color, width=1)
    draw.line([(v2, 0), (v2, h)], fill=color, width=1)
    draw.line([(0, h1), (w, h1)], fill=color, width=1)
    draw.line([(0, h2), (w, h2)], fill=color, width=1)


def draw_text_safe_areas(draw: ImageDraw.ImageDraw, w: int, h: int):
    # Title safe area near top; subtitle safe area below; CTA/footer near bottom
    overlay = (0, 0, 0, 70)
    margin = int(0.05 * w)

    # Title band (top 18% height)
    title_h = int(0.18 * h)
    title_box = (margin, margin, w - margin, margin + title_h)
    draw.rectangle(title_box, fill=overlay, outline=(255,255,255,140), width=2)
    draw_label(draw, (title_box[0] + 8, title_box[1] + 8), "Title safe area")

    # Subtitle band (next 12%)
    sub_y0 = title_box[3] + int(0.02 * h)
    sub_h = int(0.12 * h)
    subtitle_box = (margin, sub_y0, w - margin, sub_y0 + sub_h)
    draw.rectangle(subtitle_box, fill=overlay, outline=(255,255,255,120), width=2)
    draw_label(draw, (subtitle_box[0] + 8, subtitle_box[1] + 8), "Subtitle/Byline area")

    # Bottom band (footer/credit, 12%)
    foot_h = int(0.12 * h)
    foot_box = (margin, h - margin - foot_h, w - margin, h - margin)
    draw.rectangle(foot_box, fill=overlay, outline=(255,255,255,120), width=2)
    draw_label(draw, (foot_box[0] + 8, foot_box[1] + 8), "Footer/CTA area")


def main():
    parser = argparse.ArgumentParser(description="Generate cover crop guides")
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output", required=True, help="Output image path (PNG recommended)")
    parser.add_argument("--ratios", nargs="*", default=["4:3", "16:9", "1:1", "3:4"], help="Aspect ratios to draw, e.g., 4:3 16:9 1:1 3:4")
    args = parser.parse_args()

    im = Image.open(args.input).convert("RGBA")
    w, h = im.size

    # Create overlay
    overlay = Image.new("RGBA", (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    # Rule of thirds
    draw_rule_of_thirds(draw, w, h)

    # Aspect ratio boxes
    colors = [
        (0, 153, 255, 120),   # 4:3 - blue
        (0, 200, 83, 120),    # 16:9 - green
        (255, 193, 7, 120),   # 1:1 - amber
        (233, 30, 99, 120),   # 3:4 - pink
        (156, 39, 176, 120),  # fallback
    ]
    for idx, r in enumerate(args.ratios):
        try:
            rw, rh = parse_ratio(r)
        except Exception:
            continue
        x0, y0, x1, y1 = centered_box_for_ratio(w, h, rw, rh)
        color = colors[idx % len(colors)]
        draw.rectangle([x0, y0, x1, y1], outline=color, width=3)
        draw_label(draw, (x0 + 8, y0 + 8), f"{r} crop")

    # Text safe areas
    draw_text_safe_areas(draw, w, h)

    out = Image.alpha_composite(im, overlay)
    out.save(args.output)
    print(f"Saved guide to {args.output} ({w}x{h})")


if __name__ == "__main__":
    main()


