"""
Forensic Sample Dataset Generator
Creates test specimens with genuine visual patterns and tests deduplication directly on disk.
"""

import io
from PIL import Image, ImageDraw, ImageFont

def generate_sample_image(text: str, color1=(15, 32, 39), color2=(44, 83, 100), width=640, height=480, watermark=False) -> bytes:
    """Generate sample evidence image bytes using Pillow."""
    img = Image.new("RGB", (width, height), color=color1)
    draw = ImageDraw.Draw(img)

    # Draw grid
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=(40, 60, 80), width=1)
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=(40, 60, 80), width=1)

    # Target circles
    center = (width // 2, height // 2)
    draw.ellipse([center[0] - 80, center[1] - 80, center[0] + 80, center[1] + 80], outline=(0, 240, 255), width=3)
    draw.ellipse([center[0] - 40, center[1] - 40, center[0] + 40, center[1] + 40], outline=(0, 240, 255), width=2)
    draw.line([(center[0] - 110, center[1]), (center[0] + 110, center[1])], fill=(0, 240, 255), width=2)
    draw.line([(center[0], center[1] - 110), (center[0], center[1] + 110)], fill=(0, 240, 255), width=2)

    if watermark:
        draw.rectangle([20, 20, 200, 60], fill=(255, 255, 0))
        draw.text((30, 30), "DERIVATIVE", fill=(0, 0, 0))

    draw.text((width // 2 - 100, height // 2 - 130), text, fill=(255, 255, 255))
    draw.text((width // 2 - 120, height // 2 + 130), "EVIDENCE SPECIMEN", fill=(0, 240, 255))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
