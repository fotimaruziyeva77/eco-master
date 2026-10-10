"""Photos of market listings: cleaned on upload, shown through signed links.

An upload is decoded and only its pixels are drawn into a new image, so nothing the camera
wrote along (GPS position, device, time, comments) is ever stored. Links expire and are
signed for an audience: "p" links work only while the listing is public in the market,
"o" links are handed only to the owner and to moderators, for an hour.
"""

import hashlib
import hmac
import io
from dataclasses import dataclass
from typing import Literal

from PIL import Image, ImageOps, UnidentifiedImageError

from app import timeutil

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MIN_SIDE = 200
FULL_SIDE = 1280
THUMB_SIDE = 400
# A phone photo has 12–50 Mpx; anything bigger is refused before it is decoded.
MAX_PIXELS = 60_000_000
FORMATS = {"JPEG", "PNG", "WEBP"}

Size = Literal["full", "thumb"]
Audience = Literal["p", "o"]

# Public links stay the same for hours, so the browser cache keeps working.
PUBLIC_BUCKET = 6 * 3600
OWN_TTL = 3600


class PhotoError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CleanPhoto:
    full: bytes
    thumb: bytes
    width: int
    height: int


def _webp(image: Image.Image, side: int, quality: int) -> tuple[bytes, tuple[int, int]]:
    copy = image.copy()
    copy.thumbnail((side, side), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    copy.save(out, "WEBP", quality=quality, method=4)
    return out.getvalue(), copy.size


def clean_photo(data: bytes) -> CleanPhoto:
    """A JPEG/PNG/WebP upload as a metadata-free WebP photo and thumbnail, or PhotoError."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise PhotoError("photo_too_large")
    try:
        with Image.open(io.BytesIO(data)) as probe:
            if probe.format not in FORMATS:
                raise PhotoError("photo_format")
            width, height = probe.size
            if width * height > MAX_PIXELS:
                raise PhotoError("photo_too_large")
            if min(width, height) < MIN_SIDE:
                raise PhotoError("photo_too_small")
            probe.verify()
        with Image.open(io.BytesIO(data)) as source:
            if source.format == "JPEG":
                # Decode big camera photos at a reduced scale: faster and far less memory.
                source.draft("RGB", (FULL_SIDE * 2, FULL_SIDE * 2))
            source.load()
            upright = ImageOps.exif_transpose(source)
            transparent = upright.mode in ("RGBA", "LA") or (
                upright.mode == "P" and "transparency" in upright.info
            )
            # Only the pixels go on: a new image carries no EXIF, GPS, ICC profile or comments.
            clean = Image.new("RGB", upright.size, "white")
            if transparent:
                rgba = upright.convert("RGBA")
                clean.paste(rgba, mask=rgba.getchannel("A"))
            else:
                clean.paste(upright.convert("RGB"))
    except PhotoError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise PhotoError("photo_unreadable") from None
    full, size = _webp(clean, FULL_SIDE, 80)
    thumb, _ = _webp(clean, THUMB_SIDE, 75)
    return CleanPhoto(full=full, thumb=thumb, width=size[0], height=size[1])


# ---------------------------------------------------------------- signed links


def _signature(secret: str, photo_id: int, size: str, audience: str, expires: int) -> str:
    key = hashlib.sha256(b"ekoustoz-media:" + secret.encode()).digest()
    message = f"{photo_id}:{size}:{audience}:{expires}".encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()[:32]


def photo_url(secret: str, photo_id: int, size: Size, audience: Audience) -> str:
    now = int(timeutil.utc_now().timestamp())
    if audience == "p":
        expires = (now // PUBLIC_BUCKET + 2) * PUBLIC_BUCKET
    else:
        expires = (now // 600) * 600 + OWN_TTL + 600
    signature = _signature(secret, photo_id, size, audience, expires)
    return f"/api/media/{photo_id}/{size}?a={audience}&e={expires}&s={signature}"


def link_valid(
    secret: str, photo_id: int, size: str, audience: str, expires: int, signature: str
) -> bool:
    if expires < timeutil.utc_now().timestamp():
        return False
    expected = _signature(secret, photo_id, size, audience, expires)
    return hmac.compare_digest(expected, signature)
