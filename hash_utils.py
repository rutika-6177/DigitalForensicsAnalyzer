"""
Forensic Image Hashing & Analysis Utilities
Calculates SHA-256, MD5, and 64-bit Perceptual dHash, Hamming distance, and EXIF metadata.
"""

import io
import math
import hashlib
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ExifTags

def compute_hashes(image_bytes: bytes) -> Tuple[str, str]:
    """Calculate cryptographic SHA-256 and MD5 hashes."""
    sha256 = hashlib.sha256(image_bytes).hexdigest()
    md5 = hashlib.md5(image_bytes).hexdigest()
    return sha256, md5

def compute_dhash(image_bytes: bytes) -> Tuple[str, str, Dict[str, Any]]:
    """
    Computes 64-bit Difference Hash (dHash) using Pillow.
    Steps:
      1. Open image, extract dimensions, format, and EXIF.
      2. Convert to grayscale ('L').
      3. Resize to 9 columns x 8 rows.
      4. Compare adjacent horizontal pixels (P[x] > P[x+1]).
      5. Generates 64-bit binary string and 16-character hex representation.
    """
    image = Image.open(io.BytesIO(image_bytes))
    width, height = image.size
    img_format = image.format or "JPEG"

    # Compute Aspect Ratio
    gcd = math.gcd(width, height) if height > 0 else 1
    aspect_ratio = f"{width // gcd}:{height // gcd}"

    # Extract EXIF metadata if present
    device = "Forensic Station"
    exif_data = {}
    try:
        raw_exif = image.getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                exif_data[tag_name] = str(value)
            make = exif_data.get("Make", "").strip()
            model = exif_data.get("Model", "").strip()
            if make or model:
                device = f"{make} {model}".strip()
    except Exception:
        pass

    # Resize to 9x8 grayscale for dHash
    small = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())

    # Build 64-bit binary hash
    binary_bits = []
    for row in range(8):
        for col in range(8):
            left_pixel = pixels[row * 9 + col]
            right_pixel = pixels[row * 9 + col + 1]
            binary_bits.append("1" if left_pixel > right_pixel else "0")

    dhash_bin = "".join(binary_bits)

    # Convert binary to 16-hex characters
    hex_chars = []
    for i in range(0, 64, 4):
        chunk = dhash_bin[i:i + 4]
        hex_chars.append(f"{int(chunk, 2):x}")
    dhash_hex = "".join(hex_chars)

    metadata = {
        "width": width,
        "height": height,
        "dimensions": f"{width} × {height} px",
        "aspect_ratio": aspect_ratio,
        "format": img_format,
        "device": device,
        "exif": exif_data
    }

    return dhash_hex, dhash_bin, metadata

def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate the Hamming distance between two 64-bit binary strings."""
    if len(hash1) != len(hash2):
        return 64
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

def calculate_similarity(hamming_dist: int) -> int:
    """Convert Hamming distance (0..64) to a similarity percentage (0..100%)."""
    return max(0, min(100, round(((64 - hamming_dist) / 64.0) * 100)))
